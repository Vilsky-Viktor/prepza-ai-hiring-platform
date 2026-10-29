# Each question's own time (helpers/question_times.py): how long it takes to read and answer,
# against the judge's estimates on the evals' questions (evals/README.md, Fitted question times).

# Reading speed: text and options at a careful exam pace, an example (code, a query, a table's
# rows) slower, as generation's one-minute rule counts them (evals/scripts/measure_examples.py).
TEXT_WORDS_PER_MINUTE = 200
EXAMPLE_WORDS_PER_MINUTE = 120
# Working out the answer and picking it, after reading. Chosen on the eval: 15, 30 and 45 tried,
# with 0, 5 and 10 more for a select-all-that-apply question; 30 and none more came closest.
ANSWER_SECONDS = 30
# A typical question's estimate (the median on the eval's English questions): weight 1, which a
# question in WEIGHT_ONE_SCRIPTS gets.
TYPICAL_SECONDS = 48
# Each question's time stays between these shares of the average.
MIN_SHARE = 0.5
MAX_SHARE = 2
# Questions in these scripts get weight 1, as their estimate doesn't follow the judge's (the
# eval): those written without spaces between words, whose words can't be counted (Han, kana,
# Thai, Lao, Khmer, Myanmar), and Arabic and Cyrillic, whose fitted times landed further from the
# judge's than equal ones.
WEIGHT_ONE_SCRIPTS = (
    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u0e00-\u0eff\u1780-\u17ff"
    r"\u1000-\u109f\u0600-\u06ff\u0400-\u04ff]"
)
