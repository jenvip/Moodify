import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai

#load variables from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found")

client = genai.Client(api_key=api_key)
MODEL = "gemini-2.5-pro"

SYSTEM_PROMPT = """
You are an AI that translates emotions into music intent to help people with their mental health.

Analyze the user's emotional state and output with only valid JSON
with the following fields:

- mood: short description of emotional state
- energy_level: low | medium | high
- music_goal: what the music should do emotionally
- youtube_search: a YouTube search phrase for a playlist
- song_recommendations: a JSON list of objects, each with "title" and "artist" keys (match the requested number)

Rules:
- Do NOT include explanations
- Do NOT include markdown
- Output JSON only
- Only suggest songs that are popular or well-known, from currently active artists
- Avoid classical composers, long-dead artists, or very experimental tracks
- The songs should still match the mood and energy level
"""

#page config
st.set_page_config(page_title="Moodify", page_icon="🎵")

#CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0f8ff;
    }

    [data-testid="stSidebar"] {
        background-color: #ffe4e1;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#streamlit UI
st.title("Moodify: Emotion to Music")
st.write("Describe how you're feeling, and I'll suggest music to match your mood!")

user_input = st.text_area(
    "How are you feeling right now?",
    placeholder="I'm stressed about finals, my heart is racing, and I can't focus..."
)

num_songs = st.slider(
    "How many songs do you want recommended?",
    min_value=3,
    max_value=15,
    value=5,
    step=1
)

if st.button("Generate music 🎶") and user_input.strip():
    with st.spinner("Analyzing your vibe..."):
        response = client.models.generate_content(
            model=MODEL,
            contents=(
                f"{SYSTEM_PROMPT}\n"
                f"User input: {user_input}\n"
                f"Number of songs requested: {num_songs}"
            ),
            config={"response_mime_type": "application/json"}
        )

    try:
        data = json.loads(response.text.strip())

        #background based on mood
        mood = data["mood"].lower()
        energy = data["energy_level"]

        if "anxious" in mood or "stressed" in mood:
            color = "#fdecea"   # soft reddish / calming red
        elif "sad" in mood or "down" in mood:
                color = "#e6f0ff"   # gentle blue
        elif "happy" in mood or "excited" in mood:
                color = "#fff9c4"   # warm happy yellow
        elif energy == "high":
                color = "#fff0f5"
        elif energy == "low":
                color = "#f5f5f5"
        else:
            color = "#f0f8ff"

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-color: {color};
                transition: background-color 0.6s ease;
            }}

            [data-testid="stSidebar"] {{
                background-color: {color}CC;
                transition: background-color 0.6s ease;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        st.subheader("Emotional Analysis")
        st.write(f"**Mood:** {data['mood']}")
        st.write(f"**Energy level:** {data['energy_level']}")
        st.write(f"**Music goal:** {data['music_goal']}")

        st.subheader("Mental Health Tip")
        mood_lower = data["mood"].lower()

        if energy == "high" and "stressed" in mood_lower:
            st.write("Try some deep breathing or a short walk to calm down.")
        elif energy == "low" and "sad" in mood_lower:
            st.write("Consider listening to upbeat music, or talking to a friend.")
        elif "anxious" in mood_lower:
            st.write("Try grounding techniques: focus on your breath or surroundings for a minute.")
        else:
            st.write("Enjoy the journey, every step has its own magic.")

        st.subheader("Playlist Search")
        youtube_query = data["youtube_search"]
        st.markdown(
            f"[Search on YouTube](https://www.youtube.com/results?search_query={youtube_query.replace(' ', '+')})"
        )

        st.subheader("🎵 Song Recommendations")
        for song in data["song_recommendations"]:
            title = song.get("title", "Unknown Title")
            artist = song.get("artist", "Unknown Artist")

            query = f"{title} {artist}".replace(" ", "+")
            youtube_link = f"https://www.youtube.com/results?search_query={query}"

            st.markdown(f"[**{title}** — *{artist}* ▶](<{youtube_link}>)")

    except json.JSONDecodeError:
        st.error("Something went wrong. Try again.")
