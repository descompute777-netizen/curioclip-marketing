"""
Script para generar audios de Voiceover IA usando Edge-TTS (Totalmente Gratis).
Lee los guiones y genera archivos MP3 para CapCut.
"""
import os
import asyncio
import edge_tts

# Voz recomendada para datos curiosos en español (dinámica y clara)
VOICE = "es-ES-AlvaroNeural"  # Opción B: "es-MX-JorgeNeural" (Acento Latino)

GUIOS = {
    "V1_Medusa": (
        "Este animal NO puede morir. Existe un animal en el fondo del océano que es literalmente INMORTAL. "
        "La medusa Turritopsis dohrnii puede revertir su envejecimiento. Cuando está a punto de morir, se convierte de nuevo en un pólipo juvenil. "
        "Es como si un humano de 80 años pudiera convertirse en un bebé otra vez. "
        "Los científicos la están estudiando para entender si podemos usar su ADN para frenar el envejecimiento humano. "
        "¿Querrías vivir para siempre? Sígueme para más datos que vuelan la cabeza."
    ),
    "V2_Bacterias": (
        "Tu cuerpo contra la GALAXIA. La Vía Láctea tiene entre 100 y 400 MIL MILLONES de estrellas. "
        "Pero tu cuerpo tiene 38 BILLONES de bacterias. Eso es MÁS que todas las estrellas de nuestra galaxia. "
        "Solo en tu intestino hay más microorganismos que personas han existido en toda la historia de la humanidad. "
        "Técnicamente, tú eres más bacteria que humano. ¿Qué otro dato te gustaría saber?"
    ),
    "V3_RadioRusa": (
        "Esta señal lleva sonando 50 AÑOS y nadie sabe por qué. "
        "Desde 1973, una estación de radio rusa transmite un zumbido constante. 24 horas al día. 7 días a la semana. Sin parar. "
        "Se llama UVB-76, y está en un edificio militar abandonado cerca de Moscú. "
        "Pero lo más perturbador es que a veces, el zumbido se DETIENE... y una voz dice códigos y nombres en ruso. "
        "Nadie sabe quién transmite, para quién, ni por qué. Las teorías van desde comunicación con submarinos nucleares hasta "
        "un sistema 'dead man's switch' diseñado para activarse si Rusia es atacada con bombas nucleares. ¿Tú qué crees que es?"
    ),
    "V4_LeyesAbsurdas": (
        "En este país te MULTAN si no sonríes. En Pocatello, Idaho, existe una ley que dice que es ILEGAL no sonreír en público. "
        "Y no es la única ley absurda del mundo. En Singapur es ilegal masticar chicle. La multa puede ser de hasta 1,000 dólares. "
        "En Australia es ilegal vestirse de Batman o Robin. En Francia, es ilegal llamar a un cerdo 'Napoleón'. "
        "En Tailandia puedes ir a la cárcel por pisar dinero. Porque los billetes tienen la cara del Rey. "
        "¿Cuál es la más ridícula? Parte 2 si llegamos a 10K likes."
    ),
    "V5_PlomoFundido": (
        "Metió su mano en PLOMO FUNDIDO a 327 grados Celsius. "
        "Esto parece imposible, pero un fenómeno físico llamado efecto Leidenfrost lo hace posible. "
        "Cuando mojas tu mano con agua y la introduces rápidamente, la humedad crea una BARRERA de vapor que te protege por una fracción de segundo. "
        "Es el mismo principio por el que una gota de agua 'baila' sobre una sartén caliente. "
        "IMPORTANTE: esto solo funciona por milisegundos. Intentarlo sin conocimiento puede causar quemaduras de tercer grado. "
        "La física es increíble. ¿Qué experimento quieres que explique?"
    )
}

async def generate_audio(filename, text):
    output_path = os.path.join(output_dir, filename)
    communicate = edge_tts.Communicate(text, VOICE, rate="+10%") # +10% de velocidad para retención en TikTok
    await communicate.save(output_path)
    print(f"✅ Generado: {filename}")

async def main():
    tasks = []
    for title, text in GUIOS.items():
        filename = f"{title}.mp3"
        tasks.append(generate_audio(filename, text))
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(project_root, "obsidian_vault", "30_Contenido", "audios_generados")
    os.makedirs(output_dir, exist_ok=True)
    
    print("🎙️ Generando Voiceovers IA para el Sprint 1 (Acelerados al 110%)...")
    asyncio.run(main())
    print(f"\n🎉 ¡Audios listos en: {output_dir}")
