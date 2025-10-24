import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  SafeAreaView,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';

export default function HomeScreen({ navigation }) {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo/Header */}
        <View style={styles.header}>
          <MaterialIcons name="camera-alt" size={80} color="#ff6b6b" />
          <Text style={styles.title}>MagicScanner</Text>
          <Text style={styles.subtitle}>
            Scan and identify Magic: The Gathering cards
          </Text>
        </View>

        {/* Main Actions */}
        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={() => navigation.navigate('Camera')}
          >
            <MaterialIcons name="camera" size={32} color="#fff" />
            <Text style={styles.buttonText}>Scan Cards</Text>
            <Text style={styles.buttonSubtext}>Take a photo to identify cards</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={() => navigation.navigate('Collection')}
          >
            <MaterialIcons name="collections" size={32} color="#fff" />
            <Text style={styles.buttonText}>My Collection</Text>
            <Text style={styles.buttonSubtext}>View your scanned cards</Text>
          </TouchableOpacity>
        </View>

        {/* Info Cards */}
        <View style={styles.infoSection}>
          <View style={styles.infoCard}>
            <MaterialIcons name="info-outline" size={24} color="#4ecdc4" />
            <Text style={styles.infoText}>
              Take photos of multiple cards at once for faster scanning
            </Text>
          </View>
        </View>

        {/* Footer */}
        <Text style={styles.footer}>
          Powered by Scryfall API
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1e',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 60,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 20,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
    textAlign: 'center',
    marginTop: 10,
    paddingHorizontal: 40,
  },
  actions: {
    gap: 16,
  },
  button: {
    padding: 24,
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  primaryButton: {
    backgroundColor: '#ff6b6b',
  },
  secondaryButton: {
    backgroundColor: '#4ecdc4',
  },
  buttonText: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 12,
  },
  buttonSubtext: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.8,
    marginTop: 4,
  },
  infoSection: {
    marginTop: 40,
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
  },
  footer: {
    textAlign: 'center',
    color: '#666',
    fontSize: 12,
    marginTop: 'auto',
    paddingBottom: 20,
  },
});
