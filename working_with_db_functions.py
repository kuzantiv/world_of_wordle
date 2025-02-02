import sqlite3


def get_words_without_examples():
    """prints and returns list of words without examples in db"""
    with sqlite3.connect('words_with_sentence_examples.db') as con:
        records = con.execute('SELECT word '
                              'FROM words '
                              'WHERE id NOT IN (SELECT word_id FROM examples)'
                              ).fetchall()

    return records


def get_words_that_have_examples(path_to_db):
    """returns list of words that have the examples from db"""
    with sqlite3.connect(path_to_db) as con:
        con.row_factory = lambda cursor, row: row[0]
        c = con.cursor()
        records = c.execute('SELECT word '
                            'FROM words '
                            'WHERE id IN (SELECT word_id FROM examples)'
                            ).fetchall()

        return records
