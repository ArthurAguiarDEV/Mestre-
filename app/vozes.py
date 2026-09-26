"""Toca uma frase de exemplo com cada voz disponivel para voce escolher a favorita.

Roda pelo 9_escolher_voz.bat. A lista vem direto da Microsoft (precisa de internet).
"""
import asyncio
import sys

from .config import carregar_config
from .vocabulario import Vocabulario
from .voz import Voz

FRASE = "Fala, chefe! Eu sou o Mestre. Bora trabalhar? Já abri seu e-mail e o YouTube."


def vozes_disponiveis() -> list[dict]:
    import edge_tts

    todas = asyncio.run(edge_tts.list_voices())
    # Vozes em portugues + vozes "Multilingual" (de outros paises, mas falam portugues)
    return [v for v in todas if v["Locale"].startswith("pt-") or "Multilingual" in v["ShortName"]]


def main() -> None:
    try:
        vozes = vozes_disponiveis()
    except Exception as erro:
        print(f"Nao consegui baixar a lista de vozes (internet?): {erro}")
        sys.exit(1)
    vozes.sort(key=lambda v: (not v["Locale"].startswith("pt-BR"), not v["Locale"].startswith("pt-"), v["ShortName"]))
    voz = Voz(carregar_config())
    print(f"\n{len(vozes)} vozes encontradas. Vou tocar cada uma.")
    print("Aperte ENTER para ouvir a proxima, digite o NUMERO para escolher, ou S para sair.\n")
    for i, v in enumerate(vozes, 1):
        genero = "masculina" if v["Gender"] == "Male" else "feminina"
        print(f"  [{i:>2}] {v['ShortName']:<40} ({genero})")
        voz.configurar(voz=v["ShortName"])
        voz.falar(FRASE)
        resposta = input("       ENTER = proxima | numero = escolher | S = sair: ").strip().lower()
        if resposta == "s":
            break
        if resposta.isdigit() and 1 <= int(resposta) <= len(vozes):
            escolhida = vozes[int(resposta) - 1]["ShortName"]
            Vocabulario().salvar_preferencia("voz", escolhida)
            voz.configurar(voz=escolhida)
            voz.falar("Fechado! Agora essa é a minha voz.")
            print(f"\n[OK] Voz escolhida: {escolhida}")
            print("Feche e abra o Mestre para valer (ou fale: Mestre, reinicia).")
            return
    print("\nNenhuma voz escolhida. Rode de novo quando quiser.")


if __name__ == "__main__":
    main()
