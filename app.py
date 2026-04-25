import os
import asyncio
import base64
from pathlib import Path
from typing import Optional

import pymupdf4llm
import google.generativeai as genai
from nicegui import ui, events
from markdown2 import markdown

# Configuration
LOGO_PATH = Path("logo.png")

class PDFConverter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-2.5-flash" # As requested by user
        self.output_dir = str(Path.home() / "Downloads")
        self.use_ai = False
        self.current_filename = ""
        self.current_md = ""
        self.is_processing = False

    def setup_gemini(self):
        if self.api_key:
            genai.configure(api_key=self.api_key)
            return True
        return False

    async def refine_with_ai(self, text: str) -> str:
        if not self.setup_gemini():
            return text
        
        try:
            model = genai.GenerativeModel(self.model_name)
            prompt = (
                "You are an expert at cleaning up Markdown extracted from PDFs. "
                "The following text was extracted using PyMuPDF4LLM. "
                "Please fix any OCR errors, improve table formatting, and ensure the structure is logical. "
                "Keep the content exactly as is, just improve the Markdown syntax and layout.\n\n"
                f"### EXTRACTED TEXT:\n{text}"
            )
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text
        except Exception as e:
            ui.notify(f"AI Refinement failed: {str(e)}", type='negative')
            return text

    async def convert(self, file_path: str, output_area, progress, log_view):
        self.is_processing = True
        progress.visible = True
        progress.value = 0.1
        
        # Sanitize filename for Windows directory rules
        safe_name = "".join([c if c.isalnum() or c in " _-." else "_" for c in self.current_filename.rsplit('.', 1)[0]])
        target_dir = Path(self.output_dir) / safe_name
        image_subdir = "images"
        
        log_view.push(f"🚀 Starting conversion for {safe_name}")
        
        try:
            # Create target directory structure including images subdir
            img_full_path = target_dir / image_subdir
            img_full_path.mkdir(parents=True, exist_ok=True)
            log_view.push(f"📁 Created output directory: {target_dir}")
            
            # 1. Extraction with PyMuPDF4LLM (with images)
            log_view.push(f"📄 Extracting content and images to {target_dir}...")
            
            # to_markdown can handle image extraction directly
            md_text = await asyncio.to_thread(
                pymupdf4llm.to_markdown, 
                file_path, 
                write_images=True,
                image_path=str(target_dir / image_subdir),
                image_format="png"
            )
            
            progress.value = 0.5
            log_view.push(f"✅ Extraction & Images saved successful")
            
            # 2. AI Refinement (Optional)
            if self.use_ai:
                log_view.push(f"🤖 Calling {self.model_name} for refinement...")
                md_text = await self.refine_with_ai(md_text)
                log_view.push("✨ AI refinement complete")
            
            # 2.5 Fix image paths to be relative (e.g., ![](images/image-1.png))
            import re
            md_text = re.sub(r'!\[\]\((image-.*?\.png)\)', r'![](images/\1)', md_text)
            log_view.push("🔗 Image paths adjusted to relative links")
            
            self.current_md = md_text
            output_area.content = md_text
            
            # 3. Automatic Save the MD file
            md_file_path = target_dir / f"{safe_name}.md"
            with open(md_file_path, "w", encoding="utf-8") as f:
                f.write(md_text)
            
            progress.value = 1.0
            ui.notify(f"Auto-saved to {safe_name} folder", type='positive')
            log_view.push(f"🏁 Process finished. Files located at: {target_dir}")
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            log_view.push(error_msg)
            ui.notify(error_msg, type='negative')
        finally:
            self.is_processing = False
            await asyncio.sleep(1)
            progress.visible = False

converter = PDFConverter()

# --- UI Layout ---

ui.query('body').style('background: radial-gradient(circle at top right, #1a1a2e, #16213e, #0f3460); color: #e94560; font-family: "Inter", sans-serif;')

with ui.header().classes('bg-transparent backdrop-blur-md border-b border-white/10 py-4'):
    with ui.row().classes('items-center justify-between w-full px-8'):
        with ui.row().classes('items-center gap-4'):
            if LOGO_PATH.exists():
                ui.image(str(LOGO_PATH)).classes('w-12 h-12 rounded-xl shadow-lg shadow-violet-500/20')
            ui.label('PDF2MD').classes('text-3xl font-bold tracking-tight text-white')
        
        with ui.row().classes('gap-4 items-center'):
            ui.button('Documentation', icon='menu_book').props('flat').classes('text-white/70 hover:text-white')
            ui.button('GitHub', icon='code').props('flat').classes('text-white/70 hover:text-white')

with ui.row().classes('w-full h-[calc(100vh-80px)] p-8 gap-8 no-wrap'):
    
    # Sidebar / Settings
    with ui.card().classes('w-80 h-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6 shadow-2xl'):
        ui.label('SETTINGS').classes('text-xs font-black tracking-widest text-violet-400 mb-4')
        
        api_input = ui.input('Gemini API Key', password=True).bind_value(converter, 'api_key') \
            .classes('w-full mb-4').props('rounded outlined dark color=violet')
        
        model_select = ui.select(['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash-exp', 'gemini-2.5-flash'], 
                               label='Model').bind_value(converter, 'model_name') \
            .classes('w-full mb-4').props('rounded outlined dark color=violet')
        
        ui.switch('AI Refinement').bind_value(converter, 'use_ai') \
            .classes('mb-6 text-white/80')
        
        output_input = ui.input('Output Directory').bind_value(converter, 'output_dir') \
            .classes('w-full mb-4').props('rounded outlined dark color=violet') \
            .tooltip('Directory where the generated .md files will be saved')
        
        ui.separator().classes('bg-white/10 mb-6')
        
        ui.label('INFO').classes('text-xs font-black tracking-widest text-violet-400 mb-4')
        ui.label('Using PyMuPDF4LLM for high-fidelity extraction of text, tables, and images.').classes('text-white/60 text-sm italic')

    # Main Area
    with ui.column().classes('flex-grow h-full gap-6'):
        
        # Drop Zone
        with ui.card().classes('w-full p-0 overflow-hidden bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl h-48 flex items-center justify-center cursor-pointer hover:border-violet-500/50 transition-all group'):
            upload = ui.upload(label='Drop PDF here', on_upload=lambda e: handle_upload(e), auto_upload=True) \
                .classes('w-full h-full').props('flat bordered color=violet dark')
            
        progress = ui.linear_progress(value=0, show_value=False).classes('w-full h-2 rounded-full').props('color=violet dark')
        progress.visible = False
        
        # Result Area
        with ui.card().classes('w-full flex-grow bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-0 overflow-hidden'):
            with ui.tabs().classes('w-full bg-black/20 text-white') as tabs:
                preview_tab = ui.tab('PREVIEW')
                raw_tab = ui.tab('RAW MD')
            
            with ui.tab_panels(tabs, value=preview_tab).classes('w-full flex-grow bg-transparent text-white/90 p-6 overflow-auto'):
                with ui.tab_panel(preview_tab):
                    output_html = ui.markdown('').classes('markdown-body')
                with ui.tab_panel(raw_tab):
                    output_raw = ui.codemirror('', language='markdown').classes('w-full h-full').props('dark')
            
            # Action Buttons below panels
            with ui.row().classes('w-full p-4 justify-end gap-4'):
                ui.button('Open Output Folder', icon='folder_open', on_click=lambda: os.startfile(converter.output_dir)) \
                    .props('flat color=white/50')
                ui.button('Re-Save', icon='save', on_click=lambda: save_to_disk()) \
                    .props('rounded unelevated color=violet') \
                    .classes('px-6 shadow-lg shadow-violet-500/20')
        
        # Log Console
        with ui.card().classes('w-full h-32 bg-black/40 border border-white/5 rounded-2xl p-4 overflow-hidden'):
            ui.label('LOG CONSOLE').classes('text-[10px] font-black text-white/30 mb-2')
            log_view = ui.log().classes('w-full h-full text-xs font-mono text-cyan-400/80')

async def handle_upload(e: events.UploadEventArguments):
    log_view.push(f"📥 Upload event detected. Attributes: {dir(e)}")
    
    # Try to find content/file
    content = getattr(e, 'content', None) or getattr(e, 'file', None)
    
    # Try to find name/filename
    filename = getattr(e, 'name', None) or getattr(e, 'filename', None)
    if not filename and content:
        filename = getattr(content, 'name', 'temp_file.pdf')
    
    if not filename: filename = "temp_file.pdf"
    
    filename = os.path.basename(str(filename))
    converter.current_filename = filename
    temp_path = Path(f"temp_{filename}")
    log_view.push(f"📂 Preparing temp file: {temp_path}")
    
    try:
        with open(temp_path, "wb") as f:
            if hasattr(content, 'read'):
                # Handle both sync and async read()
                data = content.read()
                if asyncio.iscoroutine(data):
                    data = await data
                f.write(data)
                log_view.push("💾 Data written from content stream (async aware)")
            elif hasattr(e, 'args') and isinstance(e.args, dict):
                data = e.args.get('content') or e.args.get('file')
                if data: 
                    if asyncio.iscoroutine(data): data = await data
                    f.write(data)
                    log_view.push("💾 Data written from event args (async aware)")
    except Exception as ex:
        log_view.push(f"❌ Storage error: {str(ex)}")
        ui.notify(f"Failed to save temp file: {str(ex)}", type='negative')
        return
    
    # Update UI references
    output_html.content = "# Processing..."
    output_raw.value = "# Processing..."
    
    await converter.convert(str(temp_path), output_html, progress, log_view)
    output_raw.value = converter.current_md
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()

def save_to_disk():
    if not converter.current_md:
        ui.notify("No content to save!", type='warning')
        return
    
    try:
        out_path = Path(converter.output_dir)
        if not out_path.exists():
            out_path.mkdir(parents=True, exist_ok=True)
            log_view.push(f"📁 Created directory: {out_path}")
            
        target_name = converter.current_filename.rsplit('.', 1)[0] + ".md"
        final_file = out_path / target_name
        
        with open(final_file, "w", encoding="utf-8") as f:
            f.write(converter.current_md)
            
        log_view.push(f"💾 File saved to: {final_file}")
        ui.notify(f"Saved to {target_name}", type='positive')
    except Exception as e:
        log_view.push(f"❌ Save error: {str(e)}")
        ui.notify(f"Save failed: {str(e)}", type='negative')

# Custom CSS for the Markdown
ui.add_head_html('''
<style>
    .markdown-body {
        color: #e0e0e0 !important;
        line-height: 1.6;
    }
    .markdown-body h1, .markdown-body h2, .markdown-body h3 {
        color: #a78bfa !important;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 0.3em;
    }
    .markdown-body code {
        background-color: rgba(255,255,255,0.1);
        padding: 0.2em 0.4em;
        border-radius: 4px;
    }
    .markdown-body table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 1rem;
    }
    .markdown-body th, .markdown-body td {
        border: 1px solid rgba(255,255,255,0.1);
        padding: 0.75rem;
    }
    .markdown-body th {
        background-color: rgba(255,255,255,0.05);
    }
    .q-upload__dialog { display: none !important; }
</style>
''')

ui.run(title='PDF2MD - Premium PDF to Markdown', dark=True, port=8080)
