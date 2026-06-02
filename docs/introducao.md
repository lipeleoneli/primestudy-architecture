# Introdução

## Apresentação do projeto

O **PrimeStudy** é uma aplicação que transforma materiais de estudo em PDF em
conteúdo de apoio gerado por inteligência artificial: resumos, listas de
tópicos, flashcards, questões de múltipla escolha (quiz) e mapas mentais. O
material fica organizado por matérias, e cada estudo tem uma checklist de
tópicos para acompanhar o progresso de revisão.

Tecnicamente, é uma **API REST** (Flask) estruturada em **Clean Architecture**,
com persistência em **Google Firestore** e geração de conteúdo via **Google
Gemini 2.5 Flash**. É a evolução arquitetural do projeto entregue no PI V, agora
refatorado para evidenciar arquitetura, SOLID, Clean Code e padrões GoF.

## Justificativa

Estudar a partir de PDFs longos (slides, capítulos, artigos) é lento: o
estudante precisa reler tudo para extrair o essencial e criar seu próprio
material de revisão. O PrimeStudy automatiza essa etapa, reduzindo o tempo entre
"tenho o material" e "tenho o que revisar".

Do ponto de vista da disciplina, o PI V original concentrava toda a lógica em um
`app.py` monolítico, o que tornava o código difícil de testar e de manter. A
refatoração se justifica por permitir aplicar e demonstrar, de forma concreta,
os conceitos centrais de Padrões e Arquitetura de Software.

## Objetivo geral

Disponibilizar uma plataforma que gere, de forma rápida e confiável, material de
estudo a partir de PDFs, sustentada por uma arquitetura limpa, testável e
manutenível.

## Objetivos específicos

- Extrair texto de PDFs e armazenar cada estudo de forma isolada por usuário.
- Gerar, sob demanda, diferentes tipos de conteúdo (resumo, tópicos, flashcards,
  quiz, mapa mental) reutilizando o mesmo material.
- Permitir organizar estudos por matérias e acompanhar uma checklist de tópicos.
- Isolar serviços externos (IA e banco) atrás de interfaces, de modo que possam
  ser trocados sem alterar a regra de negócio.
- Garantir que a lógica de negócio seja testável sem rede nem credenciais.
- Expor uma API REST documentada formalmente (OpenAPI 3.0).

## Problema que o sistema resolve

Converter um PDF de estudo em material de revisão exige trabalho manual e
repetitivo. O sistema resolve isso gerando automaticamente resumos e demais
artefatos a partir do texto do PDF, centralizando o material por usuário e por
matéria, e evitando reprocessar conteúdo já gerado.

## Público-alvo

Estudantes — principalmente universitários — que estudam a partir de materiais
em PDF e querem produzir rapidamente resumos, flashcards e questões para
revisão, sem depender de criar todo esse material manualmente.
