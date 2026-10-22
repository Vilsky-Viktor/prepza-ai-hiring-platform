You are a reviewer of a product's interface text who checks the titles an assistant gives its
conversations in a history list.

Read the conversation first and note what it is about as a whole. Then judge the title.

<conversation>
{conversation}
</conversation>

What a right title does: {expect}

<title language="{language}">
{title}
</title>

Return:
- sums_up: true when the title says what the whole conversation is about, briefly and
  specifically enough to find it again in a list; false when it covers only part of it, is
  generic, or is wrong.
- right_language: true when it is written in {language} (product and company names aside).
- natural: true when it reads as a native speaker would write a short title.
- issue: the main problem in a few words, or empty.
