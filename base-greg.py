import discord
from discord.ext import commands
import json
import time
import requests
import asyncio
import re

# Bot configuration
TOKEN = ''  # Replace with your Discord bot token
OLLAMA_URL = 'http://localhost:11434'
OLLAMA_MODEL = 'llama3.1:8b'
ALLOWED_CHANNELS = [1231641639835930697, 1163975826849677373]  # Replace with your channel IDs

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Track active users to prevent multiple simultaneous requests
active_users = set()

# Configuration for iterative reasoning
MAX_STEPS = 4
SATISFACTION_THRESHOLD = 50

async def make_api_call(messages, max_tokens):
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.2
                    }
                }
            )
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

def create_step_prompt(step_number, previous_steps, original_prompt):
    if step_number == 1:
        return f"""Step 1: Analyze the following prompt and outline your initial approach:

{original_prompt}

Provide a solution and why that solution will work"""
    elif step_number < MAX_STEPS:
        return f"""Step {step_number}: Review your previous steps:

{previous_steps}

Now, critically evaluate these steps:
1. What aspects were well-addressed?
2. What aspects need improvement?
3. What new insights can you add?

Based on this evaluation, provide the next step in your reasoning."""
    else:
        return f"""Final Step: Based on all previous steps:

{previous_steps}

Synthesize everything into a comprehensive final answer. Ensure you:
1. Address any remaining gaps
2. Provide concrete conclusions
3. Offer practical next steps or recommendations if applicable"""

async def generate_response(ctx, prompt):
    thinking_msg = await ctx.send(embed=discord.Embed(title="🧠 Initializing...", description="Preparing to process your request...", color=0x3498db))
    
    all_steps = []
    messages = [{"role": "system", "content": "You are an expert AI assistant who provides detailed, thoughtful responses. Each response should be thorough yet focused on the specific step requested. do not forget the task asked. do not reiterate things too often"}]

    try:
        for step in range(1, MAX_STEPS + 1):
            # Update thinking message
            await thinking_msg.edit(embed=discord.Embed(
                title=f"🧠 Processing Step {step}/{MAX_STEPS}",
                description="Analyzing previous steps and generating next insight...",
                color=0x3498db
            ))

            # Format previous steps for context
            previous_steps = "\n\n".join([f"Step {i+1}: {step}" for i, step in enumerate(all_steps)])
            
            # Create the prompt for this step
            step_prompt = create_step_prompt(step, previous_steps, prompt)
            messages.append({"role": "user", "content": step_prompt})
            
            # Get response for this step
            step_response = await make_api_call(messages, 500)
            
            if step_response.startswith("Error:"):
                await ctx.send(embed=discord.Embed(title="❌ Error", description=step_response, color=0xe74c3c))
                return

            # Store the step response
            all_steps.append(step_response)
            messages.append({"role": "assistant", "content": step_response})

            # Create and send embed for this step
            step_embed = discord.Embed(
                title=f"{'🎯 Final Answer' if step == MAX_STEPS else f'Step {step}'}", 
                description=step_response[:4096],
                color=0x2ecc71 if step == MAX_STEPS else 0x3498db
            )
            await ctx.send(embed=step_embed)

            # If not the final step, evaluate and potentially rewrite
            if step < MAX_STEPS:
                evaluation_prompt = f"""Evaluate the current progress:

{previous_steps}

{step_response}

Rate the quality of this reasoning on a scale of 1-10 and explain why. 
If below 8, what specific improvements are needed?"""

                messages.append({"role": "user", "content": evaluation_prompt})
                evaluation = await make_api_call(messages, 300)
                messages.append({"role": "assistant", "content": evaluation})

                # Create and send evaluation embed
                eval_embed = discord.Embed(
                    title=f"📝 Evaluation of Step {step}",
                    description=evaluation[:4096],
                    color=0xe67e22
                )
                await ctx.send(embed=eval_embed)
                
                # Brief pause between steps
                await asyncio.sleep(1)

    finally:
        await thinking_msg.delete()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='think')
async def think(ctx, *, prompt: str):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        await ctx.send("❌ This command can only be used in designated channels.")
        return

    if ctx.author.id in active_users:
        await ctx.send("⏳ You already have an active request. Please wait for it to complete.")
        return

    active_users.add(ctx.author.id)
    try:
        await generate_response(ctx, prompt)
    finally:
        active_users.remove(ctx.author.id)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        return
    await ctx.send(f"⚠️ An error occurred: {str(error)}")

# Run the bot
bot.run(TOKEN)