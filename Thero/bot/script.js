const responses = {
    "sad": "I'm sorry you're feeling this way. Remember, you're not alone. ❤️",
    "depressed": "I understand that things might be tough. Talking to someone you trust can help.",
    "stressed": "Try taking deep breaths and focusing on something positive. You're doing great!",
    "anxious": "Try grounding yourself: Name 5 things you see, 4 you touch, 3 you hear, 2 you smell, and 1 you taste.",
    "alone": "You are never alone. I'm here for you. Reach out to a friend or loved one. 💙",
    "help": "If you need urgent help, please talk to someone you trust or contact a mental health professional.",
    "default": "I'm here to support you. Feel free to share your thoughts."
};

// Function to get bot response based on user input
function getBotResponse(userMessage) {
    userMessage = userMessage.toLowerCase();
    for (let keyword in responses) {
        if (userMessage.includes(keyword)) {
            return responses[keyword];
        }
    }
    return responses["default"];
}

// Function to send user message and display bot response
function sendMessage() {
    let inputField = document.getElementById("user-input");
    let userMessage = inputField.value.trim();
    
    if (userMessage === "") return; // Prevent empty messages

    // Display user message
    displayMessage(userMessage, "user-message");

    // Delay bot response for a realistic chat experience
    setTimeout(() => {
        let botResponse = getBotResponse(userMessage);
        displayMessage(botResponse, "bot-message");
    }, 500);
    
    inputField.value = ""; // Clear input field
}

// Function to display messages in the chat
function displayMessage(message, className) {
    let chatBox = document.getElementById("chat-box");
    let messageDiv = document.createElement("div");
    let messageSpan = document.createElement("span");
    
    messageSpan.textContent = message;
    messageDiv.classList.add("chat-message", className);
    messageDiv.appendChild(messageSpan);

    chatBox.appendChild(messageDiv);
    
    // Auto-scroll to the latest message
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Handle "Enter" key press to send message
function handleKeyPress(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}

// Attach keypress event listener to input field
document.getElementById("user-input").addEventListener("keypress", handleKeyPress);
