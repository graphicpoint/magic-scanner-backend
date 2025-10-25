import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { MaterialIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { scanCards } from '../services/api';

export default function CameraScreen({ navigation }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [isProcessing, setIsProcessing] = useState(false);
  const [scanMode, setScanMode] = useState('default'); // 'default' or 'pro'
  const cameraRef = useRef(null);

  // Request camera permission if not granted
  if (!permission) {
    return <View style={styles.container} />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <View style={styles.permissionContainer}>
          <MaterialIcons name="camera-alt" size={64} color="#666" />
          <Text style={styles.permissionText}>
            Camera permission is required to scan cards
          </Text>
          <TouchableOpacity
            style={styles.permissionButton}
            onPress={requestPermission}
          >
            <Text style={styles.permissionButtonText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const takePicture = async () => {
    if (!cameraRef.current) return;

    try {
      setIsProcessing(true);

      // Take photo
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        skipProcessing: false,
      });

      console.log('Photo taken:', photo.uri);

      // Send to backend for processing
      await processImage(photo.uri);

    } catch (error) {
      console.error('Error taking picture:', error);
      Alert.alert('Error', 'Failed to take picture. Please try again.');
      setIsProcessing(false);
    }
  };

  const pickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.8,
      });

      if (!result.canceled) {
        setIsProcessing(true);
        await processImage(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image. Please try again.');
    }
  };

  const processImage = async (imageUri) => {
    try {
      console.log('Processing image:', imageUri);
      console.log('Scan mode:', scanMode);

      // Call backend API with scan mode
      const results = await scanCards(imageUri, scanMode);

      console.log('Scan results:', results);

      // Navigate to results screen
      navigation.navigate('ScanResults', { results });

    } catch (error) {
      console.error('Error processing image:', error);
      
      let errorMessage = 'Failed to scan cards. Please try again.';
      
      if (error.message.includes('network')) {
        errorMessage = 'Network error. Please check your connection and backend URL.';
      } else if (error.message.includes('No cards detected')) {
        errorMessage = 'No cards detected in image. Please ensure cards are clearly visible.';
      }

      Alert.alert('Scan Failed', errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={styles.camera}
        facing="back"
      >
        {/* Overlay with guidelines */}
        <View style={styles.overlay}>
          <View style={styles.topOverlay}>
            {/* Scan Mode Toggle */}
            <View style={styles.scanModeContainer}>
              <TouchableOpacity
                style={[
                  styles.scanModeButton,
                  scanMode === 'default' && styles.scanModeButtonActive
                ]}
                onPress={() => setScanMode('default')}
                disabled={isProcessing}
              >
                <Text style={[
                  styles.scanModeText,
                  scanMode === 'default' && styles.scanModeTextActive
                ]}>
                  Default Scan
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.scanModeButton,
                  scanMode === 'pro' && styles.scanModeButtonActive
                ]}
                onPress={() => setScanMode('pro')}
                disabled={isProcessing}
              >
                <Text style={[
                  styles.scanModeText,
                  scanMode === 'pro' && styles.scanModeTextActive
                ]}>
                  Pro Scan
                </Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.instructionText}>
              Position cards within the frame
            </Text>
            <Text style={styles.subInstructionText}>
              Make sure all cards are clearly visible
            </Text>
          </View>

          {/* Frame indicator */}
          <View style={styles.frameContainer}>
            <View style={[styles.corner, styles.topLeft]} />
            <View style={[styles.corner, styles.topRight]} />
            <View style={[styles.corner, styles.bottomLeft]} />
            <View style={[styles.corner, styles.bottomRight]} />
          </View>

          {/* Bottom controls */}
          <View style={styles.controls}>
            <TouchableOpacity
              style={styles.iconButton}
              onPress={pickImage}
              disabled={isProcessing}
            >
              <MaterialIcons name="photo-library" size={32} color="#fff" />
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.captureButton, isProcessing && styles.captureButtonDisabled]}
              onPress={takePicture}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <ActivityIndicator size="large" color="#fff" />
              ) : (
                <View style={styles.captureButtonInner} />
              )}
            </TouchableOpacity>

            <View style={styles.iconButton} />
          </View>
        </View>

        {/* Processing overlay */}
        {isProcessing && (
          <View style={styles.processingOverlay}>
            <ActivityIndicator size="large" color="#ff6b6b" />
            <Text style={styles.processingText}>Processing cards...</Text>
          </View>
        )}
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#0f0f1e',
  },
  permissionText: {
    fontSize: 18,
    color: '#fff',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 30,
  },
  permissionButton: {
    backgroundColor: '#ff6b6b',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 8,
  },
  permissionButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  topOverlay: {
    alignItems: 'center',
    paddingTop: 60,
    paddingHorizontal: 20,
  },
  scanModeContainer: {
    flexDirection: 'row',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    borderRadius: 25,
    padding: 4,
    marginBottom: 20,
  },
  scanModeButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    minWidth: 120,
    alignItems: 'center',
  },
  scanModeButtonActive: {
    backgroundColor: '#ff6b6b',
  },
  scanModeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    opacity: 0.6,
  },
  scanModeTextActive: {
    opacity: 1,
  },
  instructionText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.75)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subInstructionText: {
    fontSize: 14,
    color: '#fff',
    textAlign: 'center',
    marginTop: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.75)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  frameContainer: {
    flex: 1,
    margin: 40,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: '#ff6b6b',
    borderWidth: 3,
  },
  topLeft: {
    top: 0,
    left: 0,
    borderRightWidth: 0,
    borderBottomWidth: 0,
  },
  topRight: {
    top: 0,
    right: 0,
    borderLeftWidth: 0,
    borderBottomWidth: 0,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderRightWidth: 0,
    borderTopWidth: 0,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderLeftWidth: 0,
    borderTopWidth: 0,
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingBottom: 40,
    paddingHorizontal: 20,
  },
  iconButton: {
    width: 60,
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#fff',
  },
  captureButtonDisabled: {
    opacity: 0.5,
  },
  captureButtonInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#fff',
  },
  processingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  processingText: {
    fontSize: 18,
    color: '#fff',
    marginTop: 20,
  },
});
