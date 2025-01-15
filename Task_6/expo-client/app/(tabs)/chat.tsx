import React, { useState, useEffect } from 'react';
import { View, TextInput, Button, FlatList, Text, StyleSheet, ActivityIndicator } from 'react-native';
import axios from 'axios';
import config from '../../config.json'; // Adjust the path as per your directory structure

type Message = {
  sender: string;
  content: string;
};

const ChatScreen = () => {
  const [message, setMessage] = useState('');
  const [threadId] = useState(config.thread_id); // Thread ID dynamically set from config
  const [chatHistory, setChatHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true); // State for loading indicator
  const apiUrl = config.api_url; // Use the API URL from your config file

  // Function to fetch conversation history
  const fetchConversationHistory = async () => {
    try {
      setLoading(true); // Start loading
      const response = await axios.get(`${apiUrl}/conversation-history/?thread_id=${threadId}`);
      console.log('API raw response:', response.data);
  
      // Extract the conversation history
      const { conversation_history } = response.data;
  
      // Ensure conversation_history is an array
      if (Array.isArray(conversation_history)) {
        setChatHistory(conversation_history); // Directly set the history
      } else {
        console.error('Unexpected conversation_history format:', conversation_history);
      }
    } catch (error) {
      console.error('Error fetching conversation history:', error);
    } finally {
      setLoading(false); // End loading
    }
  };
  

  // Fetch conversation history when the component mounts
  useEffect(() => {
    fetchConversationHistory();
  }, []);

  const sendMessage = async () => {
    if (message.trim() === '') return; // Avoid sending empty messages
  
    try {
      // Send the message to the API
      const response = await axios.post(`${apiUrl}/send-message/?thread_id=${threadId}&message=${message}`);
      console.log('API response for sent message:', response.data);
  
      // Update chat history with user and assistant messages
      setChatHistory((prevHistory) => [
        ...prevHistory,
        { sender: 'user', content: message },
        { sender: 'assistant', content: response.data.response },
      ]);
  
      // Clear the message input
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  // Render a single chat message
  const renderMessageItem = ({ item }: { item: Message }) => (
    <View
      style={[
        styles.messageContainer,
        item.sender === 'user' ? styles.userMessage : styles.assistantMessage,
      ]}
    >
      <Text>{item.content}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Show loading indicator while fetching chat history */}
      {loading ? (
        <ActivityIndicator size="large" color="#0000ff" />
      ) : (
        <>
          {/* Chat history */}
          <FlatList
            data={chatHistory}
            renderItem={renderMessageItem}
            keyExtractor={(item, index) => index.toString()}
            style={styles.chatHistory}
          />

          {/* Message input */}
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              value={message}
              onChangeText={setMessage}
              placeholder="Type your message..."
            />
            <Button title="Send" onPress={sendMessage} />
          </View>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 10,
    backgroundColor: '#fff',
  },
  chatHistory: {
    flex: 1,
    marginBottom: 10,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    borderColor: '#ccc',
    borderWidth: 1,
    padding: 10,
    borderRadius: 5,
    marginRight: 10,
  },
  messageContainer: {
    padding: 10,
    borderRadius: 5,
    marginVertical: 5,
  },
  userMessage: {
    backgroundColor: '#dcf8c6',
    alignSelf: 'flex-end',
  },
  assistantMessage: {
    backgroundColor: '#f1f1f1',
    alignSelf: 'flex-start',
  },
});

export default ChatScreen;
