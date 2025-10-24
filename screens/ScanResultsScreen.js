import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  Linking,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';

export default function ScanResultsScreen({ route, navigation }) {
  const { results } = route.params;
  const [selectedCards, setSelectedCards] = useState([]);

  const toggleCardSelection = (cardNumber) => {
    setSelectedCards(prev =>
      prev.includes(cardNumber)
        ? prev.filter(n => n !== cardNumber)
        : [...prev, cardNumber]
    );
  };

  const addToCollection = () => {
    if (selectedCards.length === 0) {
      Alert.alert('No Cards Selected', 'Please select at least one card to add.');
      return;
    }

    // TODO: Implement collection storage
    Alert.alert(
      'Coming Soon',
      'Collection management will be added in a future update!',
      [{ text: 'OK' }]
    );
  };

  const openScryfall = (uri) => {
    if (uri) {
      Linking.openURL(uri);
    }
  };

  const renderCard = (card) => {
    const isSelected = selectedCards.includes(card.card_number);

    if (!card.matched) {
      return (
        <View key={card.card_number} style={styles.cardContainer}>
          <View style={styles.unmatched}>
            <MaterialIcons name="error-outline" size={48} color="#666" />
            <Text style={styles.unmatchedText}>
              Card #{card.card_number} could not be identified
            </Text>
          </View>
        </View>
      );
    }

    return (
      <TouchableOpacity
        key={card.card_number}
        style={[styles.cardContainer, isSelected && styles.cardSelected]}
        onPress={() => toggleCardSelection(card.card_number)}
      >
        {/* Selection indicator */}
        <View style={styles.selectionIndicator}>
          {isSelected && (
            <MaterialIcons name="check-circle" size={24} color="#4ecdc4" />
          )}
        </View>

        {/* Card image */}
        {card.image_url && (
          <Image
            source={{ uri: card.image_url }}
            style={styles.cardImage}
            resizeMode="contain"
          />
        )}

        {/* Card details */}
        <View style={styles.cardDetails}>
          <Text style={styles.cardName}>{card.name}</Text>
          
          <View style={styles.cardMeta}>
            <Text style={styles.cardSet}>
              {card.set} ({card.set_code.toUpperCase()})
            </Text>
            {card.collector_number && (
              <Text style={styles.cardNumber}>
                #{card.collector_number}
              </Text>
            )}
          </View>

          {card.rarity && (
            <View style={[styles.rarityBadge, styles[`rarity${card.rarity}`]]}>
              <Text style={styles.rarityText}>
                {card.rarity.toUpperCase()}
              </Text>
            </View>
          )}

          {/* Prices */}
          {card.prices && (
            <View style={styles.priceSection}>
              <Text style={styles.priceLabel}>Prices:</Text>
              <View style={styles.priceGrid}>
                {card.prices.usd && (
                  <Text style={styles.priceText}>
                    💵 ${card.prices.usd}
                  </Text>
                )}
                {card.prices.eur && (
                  <Text style={styles.priceText}>
                    💶 €{card.prices.eur}
                  </Text>
                )}
                {card.prices.tix && (
                  <Text style={styles.priceText}>
                    🎫 {card.prices.tix} tix
                  </Text>
                )}
              </View>
            </View>
          )}

          {/* Confidence */}
          <View style={styles.confidenceBar}>
            <Text style={styles.confidenceLabel}>
              Match Confidence: {card.confidence}%
            </Text>
            <View style={styles.confidenceBarBackground}>
              <View
                style={[
                  styles.confidenceBarFill,
                  { width: `${card.confidence}%` }
                ]}
              />
            </View>
          </View>

          {/* Actions */}
          <TouchableOpacity
            style={styles.scryfallButton}
            onPress={() => openScryfall(card.scryfall_uri)}
          >
            <MaterialIcons name="open-in-new" size={16} color="#4ecdc4" />
            <Text style={styles.scryfallButtonText}>
              View on Scryfall
            </Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Summary header */}
        <View style={styles.header}>
          <Text style={styles.title}>Scan Complete</Text>
          <Text style={styles.summary}>
            Found {results.cards_found} card{results.cards_found !== 1 ? 's' : ''}
            {', '}
            matched {results.cards_matched}
          </Text>
        </View>

        {/* Cards list */}
        <View style={styles.cardsList}>
          {results.cards.map(renderCard)}
        </View>
      </ScrollView>

      {/* Bottom action bar */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.bottomButton}
          onPress={() => navigation.navigate('Camera')}
        >
          <MaterialIcons name="camera-alt" size={24} color="#fff" />
          <Text style={styles.bottomButtonText}>Scan More</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.bottomButton, styles.bottomButtonPrimary]}
          onPress={addToCollection}
        >
          <MaterialIcons name="add" size={24} color="#fff" />
          <Text style={styles.bottomButtonText}>
            Add to Collection ({selectedCards.length})
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1e',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  summary: {
    fontSize: 16,
    color: '#aaa',
  },
  cardsList: {
    padding: 16,
    gap: 16,
  },
  cardContainer: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  cardSelected: {
    borderColor: '#4ecdc4',
  },
  selectionIndicator: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 1,
  },
  cardImage: {
    width: '100%',
    height: 300,
    borderRadius: 8,
    marginBottom: 16,
  },
  cardDetails: {
    gap: 12,
  },
  cardName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  cardMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardSet: {
    fontSize: 14,
    color: '#aaa',
  },
  cardNumber: {
    fontSize: 14,
    color: '#666',
  },
  rarityBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 4,
  },
  raritycommon: {
    backgroundColor: '#333',
  },
  rarityuncommon: {
    backgroundColor: '#4a5568',
  },
  rarityrare: {
    backgroundColor: '#805ad5',
  },
  raritymythic: {
    backgroundColor: '#dd6b20',
  },
  rarityText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#fff',
  },
  priceSection: {
    gap: 8,
  },
  priceLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#aaa',
  },
  priceGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  priceText: {
    fontSize: 14,
    color: '#4ecdc4',
    fontWeight: '600',
  },
  confidenceBar: {
    gap: 4,
  },
  confidenceLabel: {
    fontSize: 12,
    color: '#888',
  },
  confidenceBarBackground: {
    height: 6,
    backgroundColor: '#333',
    borderRadius: 3,
    overflow: 'hidden',
  },
  confidenceBarFill: {
    height: '100%',
    backgroundColor: '#4ecdc4',
  },
  scryfallButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 8,
  },
  scryfallButtonText: {
    fontSize: 14,
    color: '#4ecdc4',
    fontWeight: '600',
  },
  unmatched: {
    alignItems: 'center',
    padding: 40,
  },
  unmatchedText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 12,
  },
  bottomBar: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: '#222',
  },
  bottomButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    borderRadius: 8,
    backgroundColor: '#333',
  },
  bottomButtonPrimary: {
    backgroundColor: '#ff6b6b',
  },
  bottomButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
