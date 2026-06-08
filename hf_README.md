---
title: Ragmate
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# ragmate

**A Retrieval-Augmented Generation (RAG) system for chatting with your documents.**

Upload PDFs, Word docs, Markdown, or plain text and ask questions in natural language. ragmate embeds documents into a vector store, retrieves the most semantically relevant passages at query time, and passes them as context to Gemini to generate grounded answers with source citations.

## Usage

1. Enter your `API_KEY` in the header (provided by the Space owner)
2. Upload a document (PDF, DOCX, Markdown, or TXT) - up to 20 MB
3. Ask questions in the chat

> Note: uploaded documents are stored in memory and will be lost when the Space restarts.

## Tech stack

FastAPI + ChromaDB + Gemini 2.5 Flash + gemini-embedding-001

Source: [github.com/rajeshsub/ragmate](https://github.com/rajeshsub/ragmate)
