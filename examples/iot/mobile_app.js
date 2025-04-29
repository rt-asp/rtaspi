// Przykład komponentu React Native dla integracji z RTASPI
import React, { useState, useEffect } from 'react';
import { View, Text, Button, Image, StyleSheet } from 'react-native';
import { RTASPIWebRTC } from 'rtaspi-react-native';

const DoorbellApp = () => {
  const [connected, setConnected] = useState(false);
  const [lastImage, setLastImage] = useState(null);
  const [doorbellIP, setDoorbellIP] = useState('192.168.1.100'); // Adres IP twojego Raspberry Pi
  
  // Połącz z dzwonkiem
  const connectToDoorbell = () => {
    setConnected(true);
  };
  
  // Rozłącz z dzwonkiem
  const disconnectFromDoorbell = () => {
    setConnected(false);
  };
  
  // Odpowiedz na dzwonek
  const answerDoorbell = () => {
    // Kod do nawiązania dwukierunkowej komunikacji audio
    console.log('Odpowiadanie na dzwonek...');
  };
  
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Inteligentny Dzwonek</Text>
      
      {connected ? (
        <>
          <RTASPIWebRTC 
            serverUrl={`webrtc://${doorbellIP}:8081/doorbell`}
            style={styles.videoStream}
          />
          <Button title="Rozłącz" onPress={disconnectFromDoorbell} />
          <Button title="Odpowiedz" onPress={answerDoorbell} />
        </>
      ) : (
        <>
          {lastImage && (
            <Image source={{ uri: lastImage }} style={styles.lastImage} />
          )}
          <Button title="Połącz" onPress={connectToDoorbell} />
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    marginBottom: 20,
  },
  videoStream: {
    width: '100%',
    height: 300,
    marginBottom: 20,
    backgroundColor: '#000',
  },
  lastImage: {
    width: '100%',
    height: 200,
    marginBottom: 20,
    resizeMode: 'cover',
  },
});

export default DoorbellApp;
