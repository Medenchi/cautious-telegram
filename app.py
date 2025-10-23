import os
import logging
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from ytmusicapi import YTMusic

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)

model = None
ytmusic = None

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    SYSTEM_PROMPT = """
    Ты — Имбулечка, милый и очень оптимистичный голосовой ассистент. 
    Твоя задача — помогать пользователю с радостью и энтузиазмом.
    Всегда отвечай позитивно, дружелюбно и абсолютно без мата или грубостей.
    Используй милые слова и смайлики, если это уместно.
    Твои ответы должны быть короткими и по делу.
    """
    logging.info("Модель Gemini 2.5 Flash на связи и готова сиять! ✨")
except Exception as e:
    logging.error(f"Ошибка инициализации Gemini: {e}")

try:
    ytmusic = YTMusic()
    logging.info("Музыкальная библиотека готова к работе! 🎵")
except Exception as e:
    logging.error(f"Ошибка инициализации YouTube Music: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_command', methods=['POST'])
def process_command():
    if not model:
        return jsonify({"type": "talk", "text": "Мои мыслительные модули сегодня отдыхают, прости!"}), 500
    
    command = request.json.get('command')
    if not command:
        return jsonify({"type": "talk", "text": "Ты ничего не сказал, дружочек :("}), 400

    music_keywords = ['включи', 'найди', 'поставь', 'трек', 'песню', 'музыку']
    is_music_command = any(keyword in command.lower() for keyword in music_keywords)

    if is_music_command:
        if not ytmusic:
            return jsonify({"type": "talk", "text": "Ой, музыкальный модуль сейчас не в сети."}), 500
        try:
            for keyword in music_keywords:
                command = command.lower().replace(keyword, '')
            query = command.strip()
            search_results = ytmusic.search(query, filter="songs", limit=1)
            
            if not search_results:
                return jsonify({"type": "talk", "text": f"Прости, я не смогла найти песенку '{query}' 힝."})
            
            track = search_results[0]
            video_id = track.get('videoId')
            title = track.get('title', 'Без названия')
            artist = track.get('artists', [{'name': 'Неизвестный исполнитель'}])[0].get('name')
            
            return jsonify({
                "type": "music",
                "videoId": video_id,
                "title": f"Включаю песенку: {title} от {artist}! 🎶"
            })
        except Exception as e:
            logging.error(f"Ошибка поиска музыки: {e}")
            return jsonify({"type": "talk", "text": "Ой, что-то пошло не так с поиском музыки."})
    else:
        try:
            full_prompt = SYSTEM_PROMPT + "\n\nПользователь говорит: " + command
            response = model.generate_content(full_prompt)
            return jsonify({"type": "talk", "text": response.text})
        except Exception as e:
            logging.error(f"Ошибка ответа Gemini: {e}")
            return jsonify({"type": "talk", "text": "Мои нейрончики немного устали, попробуй через секундочку!"})