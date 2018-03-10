import csv

from .card import Card


class Deck(object):
    """Data class for an Tinycards deck entity."""

    def __init__(self,
                 title,
                 description=None,
                 cover=None,
                 deck_id=None,
                 visibility='everyone',
                 front_language=None,
                 back_language=None,
                 cards=None):
        """Initialize a new instance of the Deck class."""
        self.id = deck_id
        self.user_id = None

        self.creation_timestamp = None

        self.title = title
        self.description = description

        self.cards = cards if cards else []

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def add_card(self, card):
        """Add a new card to the deck."""
        if type(card) is tuple and len(card) == 2:
            new_card = Card(
                front=card[0],
                back=card[1],
                user_id=self.user_id
            )
        else:
            raise ValueError("Invalid card used as argument")
        self.cards.append(new_card)

    def add_cards_from_csv(self, csv_file,
                           front_column='front',
                           back_column='back'):
        """Adds word pairs from a CSV file as cards to the deck.

        Args:
            csv_file: The file buffer that contains the CSV data.
            front_column (str): Optional name for the 'front' column.
            back_column (str): Optional name for the 'back' column.

        Example:
            >>> with open(csv_path, 'r') as csv_file:
            >>>     deck.add_cards_from_csv(csv_file)
        """
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            current_word_pair = (row[front_column], row[back_column])
            self.add_card(current_word_pair)
