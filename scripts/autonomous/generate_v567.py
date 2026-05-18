"""
Genera voiceovers + SRT para V5 Tunguska, V6 Conan bacterium, V7 Cosquillas.
"""
import sys, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
sys.path.insert(0, str(ROOT))
AUDIO_DIR = ROOT / "obsidian_vault" / "30_Contenido" / "audios_generados"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

VOICE = "es-MX-JorgeNeural"
RATE = "+10%"

# Voiceovers — guion completo (HOOK + IDENTIFICACION + PROMESA + DESARROLLO + CTA)
GUIONES = {
    "V5_Tunguska": (
        "El 30 de junio de 1908, algo destruyo 2,000 kilometros cuadrados de bosque en Siberia. "
        "En 113 anos nadie ha podido explicar exactamente que fue. "
        "No hubo crater. No hubo meteorito. Solo el bosque arrasado, millones de arboles caidos "
        "en la misma direccion y una ola de calor que se sintio a 60 kilometros. "
        "La explosion fue mil veces mas poderosa que la bomba de Hiroshima. "
        "Si hubiera impactado tres horas despues, habria destruido San Petersburgo. "
        "Los cientificos tardaron 19 anos en llegar al lugar. Encontraron el bosque caido en patrones de mariposa. "
        "Como si algo hubiera explotado en el aire, no debajo. En el aire. "
        "Las teorias van desde un cometa de hielo que se vaporizo antes de impactar, hasta una explosion de antimateria. "
        "La teoria oficial mas aceptada: un asteroide que exploto a 10 kilometros de altura. "
        "Pero no hay fragmentos. Ninguno. 113 anos despues, el caso sigue oficialmente abierto. "
        "Y lo mas perturbador: en 2013 otro objeto similar entro sobre Chelyabinsk, Rusia. Nadie lo vio venir."
    ),
    "V6_Conan": (
        "Existe una bacteria que puede sobrevivir a la explosion de una bomba nuclear. "
        "La apodaron Conan The Bacterium. "
        "Puede absorber un millon y medio de rads de radiacion sin morir. "
        "Una dosis de 500 rads mata a un ser humano. Esta bacteria necesita 3,000 veces mas para siquiera sentirlo. "
        "Tiene el sistema de reparacion de ADN mas sofisticado que existe en la naturaleza. "
        "Cuando la radiacion destroza su ADN, lo reconstruye completo en horas. "
        "En 1956 unos cientificos esterilizaban carne enlatada con radiacion. "
        "La dosis era suficiente para matar cualquier forma de vida conocida. "
        "Cuando abrieron las latas, la carne se habia echado a perder. Alguien habia sobrevivido. "
        "Hoy los cientificos estudian su mecanismo. Si pudieramos copiarlo en celulas humanas "
        "podriamos curar dano por radiacion, cancer y envejecimiento. "
        "Una bacteria lleva 3,000 millones de anos perfeccionando lo que nosotros llevamos 70 anos tratando de entender."
    ),
    "V7_Cosquillas": (
        "Prueba esto ahora mismo: intenta hacerte cosquillas a ti mismo. "
        "Funciono? No. Nunca funciona. "
        "Tu cerebro puede predecir exactamente lo que vas a sentir antes de que lo sientas. "
        "Se llama prediccion sensorial. Tu cerebro tiene un modelo de tu cuerpo tan preciso "
        "que sabe lo que vas a tocar antes de tocarlo. "
        "Por eso las cosquillas de otra persona si funcionan: ese modelo no puede predecir movimientos externos. "
        "Pero hay un truco. Si usas un robot con delay de 200 milisegundos para hacerte cosquillas, si funcionan. "
        "El cerebro no puede predecir el retraso. Guarda esto para probarlo."
    ),
}


def ensure_edge_tts():
    try:
        import edge_tts
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts", "-q"], check=True)
        import edge_tts
    return edge_tts


async def generate_one(name: str, text: str):
    edge_tts = ensure_edge_tts()
    out = AUDIO_DIR / f"{name}.mp3"
    print(f"[TTS] {name} ({len(text)} chars) -> {out.name}")
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
    await communicate.save(str(out))
    kb = out.stat().st_size // 1024
    print(f"[OK]  {out.name} = {kb} KB")
    return out


async def main():
    for name, text in GUIONES.items():
        await generate_one(name, text)


if __name__ == "__main__":
    asyncio.run(main())
    print("\n=== Voiceovers generados ===")
    for name in GUIONES:
        p = AUDIO_DIR / f"{name}.mp3"
        if p.exists():
            print(f"  OK {p}")
        else:
            print(f"  FAIL {p}")
