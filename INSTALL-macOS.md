# Instalar o Clippa no macOS

Este guia vale para o arquivo pronto:

- `Clippa-mac-unsigned.zip`

## Instalação

1. Baixe `Clippa-mac-unsigned.zip`
2. Dê duplo clique no zip para extrair
3. Arraste `Clippa.app` para `Applications`
4. Abra a pasta `Applications`
5. Clique com o botão direito em `Clippa.app`
6. Escolha `Open`
7. Confirme o aviso do macOS

Essa primeira abertura manual é esperada, porque a build pública atual não é notarizada pela Apple.

## Se o macOS bloquear

1. Tente abrir `Clippa.app`
2. Abra `System Settings`
3. Vá em `Privacy & Security`
4. Role até a seção de segurança
5. Clique em `Open Anyway`
6. Tente abrir o app novamente

## O que esperar

- o Clippa abre como um app normal de macOS
- os arquivos são salvos pelo diálogo nativo de salvar
- os temporários ficam em `~/Downloads/Clippa`

## Se você quiser uma instalação sem aviso no futuro

O repo já inclui scripts para code signing e notarização, mas isso exige uma conta Apple Developer.
