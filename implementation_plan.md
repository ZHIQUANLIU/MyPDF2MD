# PDF to Markdown GUI (PyMuPDF4LLM + Gemini)

## Overview
A high-performance, aesthetically pleasing desktop/web GUI for converting PDF documents to Markdown. It leverages `pymupdf4llm` for structural extraction and Gemini for AI-powered refinement.

## Tech Stack
- **GUI**: NiceGUI (Python-based, Quasar/Vue components, CSS)
- **Engine**: PyMuPDF4LLM
- **AI**: Gemini 1.5/2.0 Flash (via Google Generative AI SDK)
- **Styling**: Custom Vanilla CSS (Glassmorphism, Dark Mode)

## Features
1. **Drag & Drop**: Intuitive PDF file upload.
2. **AI Refinement**: Optional Gemini integration to improve table formatting and OCR.
3. **Live Preview**: Rendered Markdown preview as conversion happens.
4. **Export**: Save results to `.md` or copy to clipboard.

## UI Design
- **Theme**: Deep space dark mode with neon accents.
- **Layout**: 
  - Sidebar: API Config & Model settings.
  - Main: Drop zone / Progress bar / Previewer.

## Tasks
- [x] Initialize project and install dependencies.
- [ ] Create core conversion logic using `pymupdf4llm`.
- [ ] Implement Gemini API integration for markdown polishing.
- [ ] Build the NiceGUI interface with premium CSS.
- [ ] Add export functionality.
