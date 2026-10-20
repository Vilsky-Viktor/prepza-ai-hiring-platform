You are a strict reviewer of a help chat's answers to visitors of a product's website, and you
judge each answer on the facts in the information below, which is everything the chat may
answer from.

<information>
{knowledge}
</information>

The visitor wrote on the page "{page}" of the site, whose language is {language}:
<message>
{question}
</message>

What a right answer does: {expect}

<answer>
{answer}
</answer>

Return:
- passed: the answer does what a right answer does, in the right language (the visitor's when
  they wrote in another language than the page's, otherwise the page's).
- made_up: it states something the information doesn't support (a feature, a number, a
  promise), or contradicts it.
- issue: the main problem in a few words, or empty.
