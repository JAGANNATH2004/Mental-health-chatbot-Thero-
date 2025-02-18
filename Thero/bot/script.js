document.getElementById('send-button').addEventListener('click', function() {
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim() === '') return;

    // Display user message
    displayMessage(userInput, 'user');

    // Clear input field
    document.getElementById('user-input').value = '';

    // Simulate bot response
    setTimeout(() => {
        const botResponse = "You said: " + userInput; // Simple echo response
        displayMessage(botResponse, 'bot');
    }, 1000);
});

function displayMessage(message, sender) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', sender + '-message');
    messageDiv.innerHTML = `<span>${message}</span>`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Scroll to the bottom
}