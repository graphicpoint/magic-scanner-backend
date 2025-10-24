import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';

export default function CollectionScreen({ navigation }) {
  // TODO: Implement collection storage with Supabase
  // For now, show placeholder

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Empty state */}
        <View style={styles.emptyState}>
          <MaterialIcons name="collections" size={80} color="#666" />
          <Text style={styles.emptyTitle}>No Cards Yet</Text>
          <Text style={styles.emptyText}>
            Start scanning cards to build your collection!
          </Text>
          
          <TouchableOpacity
            style={styles.scanButton}
            onPress={() => navigation.navigate('Camera')}
          >
            <MaterialIcons name="camera-alt" size={24} color="#fff" />
            <Text style={styles.scanButtonText}>Scan Cards</Text>
          </TouchableOpacity>
        </View>

        {/* Coming soon features */}
        <View style={styles.featuresSection}>
          <Text style={styles.featuresTitle}>Coming Soon:</Text>
          
          <View style={styles.featureItem}>
            <MaterialIcons name="storage" size={24} color="#4ecdc4" />
            <View style={styles.featureText}>
              <Text style={styles.featureName}>Collection Storage</Text>
              <Text style={styles.featureDesc}>
                Save and organize your scanned cards
              </Text>
            </View>
          </View>

          <View style={styles.featureItem}>
            <MaterialIcons name="search" size={24} color="#4ecdc4" />
            <View style={styles.featureText}>
              <Text style={styles.featureName}>Search & Filter</Text>
              <Text style={styles.featureDesc}>
                Find cards by name, set, or color
              </Text>
            </View>
          </View>

          <View style={styles.featureItem}>
            <MaterialIcons name="bar-chart" size={24} color="#4ecdc4" />
            <View style={styles.featureText}>
              <Text style={styles.featureName}>Collection Stats</Text>
              <Text style={styles.featureDesc}>
                View total value and rarity distribution
              </Text>
            </View>
          </View>

          <View style={styles.featureItem}>
            <MaterialIcons name="share" size={24} color="#4ecdc4" />
            <View style={styles.featureText}>
              <Text style={styles.featureName}>Export & Share</Text>
              <Text style={styles.featureDesc}>
                Export your collection to CSV or share with friends
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1e',
  },
  content: {
    flexGrow: 1,
    padding: 20,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#aaa',
    textAlign: 'center',
    marginTop: 12,
    paddingHorizontal: 40,
  },
  scanButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#ff6b6b',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 8,
    marginTop: 30,
  },
  scanButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  featuresSection: {
    marginTop: 40,
    gap: 16,
  },
  featuresTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 12,
  },
  featureText: {
    flex: 1,
    gap: 4,
  },
  featureName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  featureDesc: {
    fontSize: 14,
    color: '#aaa',
    lineHeight: 20,
  },
});
