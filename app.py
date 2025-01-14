import streamlit as st
from newspaper import Article, Config
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import spacy
import re

# Download necessary NLTK resources
nltk.download('punkt')

# Load the spaCy English model
nlp = spacy.load('en_core_web_sm')

# Configure user-agent for newspaper3k
config = Config()
config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

# Define trigger words
trigger_words = [
    'announced', 'passed', 'introduced', 'unveiled', 'declared', 'debated', 'discussed', 'hearing',
    'reviewed', 'rejected', 'voted', 'implemented', 'enforced', 'issued', 'ruled', 'guideline',
    'regulation', 'challenged', 'appealed', 'protested', 'supported', 'poll', 'report', 'study',
    'signed', 'agreed', 'treaty', 'consultation', 'emergency', 'imposed', 'urgent', 'order', 'plan',
    'sit-in', 'striked', 'okayed', 'formed', 'rallies'
]
trigger_pattern = re.compile(r'\b(?:' + '|'.join(trigger_words) + r')\b', re.IGNORECASE)

# Streamlit UI
st.title("Event Extractor from News Articles")

# URL input field
url = st.text_input("Enter the URL of the news article:", "")

# Slider for MAX_EVENT_SENTENCES
max_event_sentences = st.slider("Maximum number of sentences for event description:", min_value=1, max_value=10, value=4)

# Submit button
if st.button("Submit"):
    if url:
        try:
            # Fetch and parse the article
            article = Article(url, config=config)
            article.download()
            article.parse()

            # Split the article into sentences
            sentences = sent_tokenize(article.text)

            # Find sentences containing any of the event trigger words
            event_sentences = [sentence for sentence in sentences if trigger_pattern.search(sentence)]
            
            # Limit the event description
            event_description = ' '.join(event_sentences[:max_event_sentences]) if event_sentences else 'No specific event mentioned'

            # Identify event types by finding trigger words in the text
            event_triggers = [word for word in word_tokenize(article.text.lower()) if word in trigger_words]
            event_type = ', '.join(set(event_triggers)) if event_triggers else 'None'

            # Process the article text with spaCy to extract named entities
            doc = nlp(article.text)
            entities = [(ent.text, ent.label_) for ent in doc.ents]

            # Extract arguments: Actor, Action, Target, Location, Time
            arguments = {
                "Actor": [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "NORP"]],
                "Action": event_triggers,
                "Target": [ent.text for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]],
                "Location": [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]],
                "Time": [ent.text for ent in doc.ents if ent.label_ == "DATE"]
            }

            # Check if the publish date is available; if not, try to extract it from the text
            publish_date = article.publish_date
            if not publish_date:
                # Attempt to find dates within the first few lines of the text
                date_entities = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
                publish_date = date_entities[0] if date_entities else "Unknown"

            # Display results
            st.subheader("Results")
            st.write("**Title:**", article.title)
            st.write("**Event Type:**", event_type)
            st.write("**Event Description:**", event_description)
            st.write("**Entities:**", entities)
            st.write("**Arguments:**", arguments)
            st.write("**Publish Date:**", publish_date)
            st.write("**URL:**", url)

        except Exception as e:
            st.error(f"Failed to process the URL. Error: {e}")
    else:
        st.error("Please enter a valid URL.")
