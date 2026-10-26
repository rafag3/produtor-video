# Rafa Video Studio AI V2

## Novidades
- Timeline visual com régua, blocos e playhead sincronizado
- Clique na timeline para navegar
- Divisão do segmento no playhead
- Exclusão e reordenação de segmentos
- Undo/redo
- Auto Cut por silêncio com limiar, duração mínima, margem e revisão antes de aplicar
- Detecção de cenas refletida na timeline
- Reprodução sequencial dos segmentos
- Exportação final por FFmpeg
- Projetos JSON e originais preservados

## Instalação
1. Instale Python 3.12.
2. Execute `install_windows.bat`.
3. Se necessário: `winget install Gyan.FFmpeg`.
4. Reabra o terminal e execute `run_windows.bat`.

## Corte manual
1. Adicione um vídeo.
2. Clique na timeline para posicionar o playhead.
3. Clique em `Dividir no playhead`.
4. Selecione um bloco e use `Excluir segmento`.
5. Use undo/redo se necessário.

## Corte automático
Selecione um segmento e clique em `Auto corte de silêncio`. Revise os intervalos encontrados antes de aplicar.

## Limitações conhecidas
- A timeline V2 usa blocos e nomes, sem miniaturas de frames.
- Transições, textos e efeitos em trilhas ainda não são renderizados nesta versão.
- O Whisper pode baixar o modelo no primeiro uso.
