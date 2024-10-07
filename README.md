Hello! Welcome to Greg 🤖  
Greg is a discord chatbot powered by [Ollama](https://github.com/ollama/ollama) For the [Chris Tech Tips community](https://discord.gg/qUTvJbDWMu)  
WIP - Also currently waiting on response from owner of Gregtech imagery to see if we need to change it  
  
__Features__  
Option for o1-like reasoning - Currently implemented as main chat function (its pretty bad)  

 
__Features to work on__  
- Chat history for normal chats and o1-like chats - needs severe improvement and honestly I wouldn't mind rewriting the entire thing, its all garbage rn  
- Some way to optimize load on the systems running the models - electricity isn't free!  
- Switching between ollama instances incase there is a failure - for an example; falling back onto a CPU only instance if the GPU instance goess offline
- cooldowns - bigger more expensive models should require cooldowns in order to keep things smooth
- possible integration with Discord threads (is this possible?) - a user is able to use a slash command in order to start a thread with greg for a semi private chat 
