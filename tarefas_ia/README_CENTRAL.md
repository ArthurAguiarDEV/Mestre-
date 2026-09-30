# Central de tarefas por IA

Esta central não envia mensagens automaticamente para Claude, Manus ou ChatGPT.
Ela cria os arquivos que permitem trabalhar de forma organizada e gratuita.

## Criar uma tarefa

```powershell
cd C:\Ias\Mestre-repo\agentes_crewai
..\venv\Scripts\python.exe central_tarefas.py "Descreva aqui a melhoria desejada"
```

## Depois de criar

1. Abra `tarefas_ia\claude\hoje.md`, `manus\hoje.md` ou `chatgpt\hoje.md`.
2. Abra o prompt indicado em `tarefas_ia\prompts_prontos\`.
3. Copie o prompt para o novo chat da IA correspondente.
4. Salve o retorno em `tarefas_ia\resultados\`.
5. Registre feedback em `tarefas_ia\feedback\`.

O arquivo da fila é a fonte oficial da tarefa. O GitHub só entra depois de o usuário
testar e escrever `OK para publicar`.
