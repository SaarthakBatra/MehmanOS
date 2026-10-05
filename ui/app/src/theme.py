import streamlit as st
import datetime

HEADER_H = 84      # px, fixed header
BAR_H = 120        # px, reserved for the bottom bar (input row + padding)

CSS = f"""
<style>
:root {{ color-scheme: dark; --hdr:{HEADER_H}px; --bar:{BAR_H}px; }}
html, body {{  }}
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:#000 !important; }}
[data-testid="stApp"] p, [data-testid="stApp"] span, [data-testid="stApp"] label, [data-testid="stApp"] li,
[data-testid="stApp"] h2, [data-testid="stApp"] h3, [data-testid="stMarkdownContainer"] {{ color:#e5e7eb; }}
[data-testid="stHeader"], [data-testid="stSidebarCollapsedControl"] {{ display:none; }}

/* Restore standard scrolling mechanics for the main container */
[data-testid="stMain"] {{
  position: relative !important;
  height: 100vh !important;
}}

[data-testid="stMainBlockContainer"] {{
  height: calc(100vh - var(--bar)) !important;
  max-height: calc(100vh - var(--bar)) !important;
  overflow-y: auto !important;
  position: relative; z-index: 10; box-sizing: border-box;
  width: 100%; max-width: 1100px; margin: 0 auto;
  padding: calc(var(--hdr) + 12px) 16px 24px 16px !important;
}}

/* Top Right Menu Container */
.st-key-top_right_menu {{
  position: fixed !important;
  top: 18px !important;
  right: 24px !important;
  left: auto !important;
  width: 50px !important;
  height: 50px !important;
  z-index: 1000 !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  pointer-events: none !important;
}}
.st-key-top_right_menu [data-testid="stPopover"] button {{
  background: transparent !important;
  border: none !important;
  color: #fff !important;
  font-size: 1.5rem !important;
  padding: 0 !important;
  pointer-events: auto !important;
}}
.st-key-top_right_menu [data-testid="stPopover"] button svg {{
  display: none !important;
}}
.blob{{position:fixed;border-radius:50%;filter:blur(120px);mix-blend-mode:screen;pointer-events:none;z-index:0}}
.b1{{top:10%;left:10%;width:35rem;height:35rem;background:rgba(148,17,203,.4);animation:b1 15s infinite alternate ease-in-out}}
.b2{{top:30%;right:10%;width:30rem;height:30rem;background:rgba(65,112,138,.5);animation:b2 12s infinite alternate ease-in-out}}
@keyframes b1{{0%{{transform:translate(0,0)}}100%{{transform:translate(30vw,20vh)}}}}
@keyframes b2{{0%{{transform:translate(0,0)}}100%{{transform:translate(-30vw,-20vh)}}}}
.mh-header{{position:fixed;pointer-events:none;top:0;left:0;width:100%;height:var(--hdr);z-index:50;display:flex;align-items:center;
  justify-content:space-between;padding:0 clamp(12px,2vw,32px);border-bottom:1px solid rgba(255,255,255,.1);
  background:rgba(0,0,0,.4);backdrop-filter:blur(16px);box-sizing:border-box}}
.mh-header h1{{margin:0;font-size:clamp(2.8rem,3vw,5.0rem) !important;font-weight:900;letter-spacing:-.04em;color:#fff}}
.mh-pill{{pointer-events:auto;padding:8px 18px;border-radius:999px;background:rgba(0,0,0,.9);border:1px solid rgba(255,255,255,.1);
  font-size:.7rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#fff;white-space:nowrap;display:flex;gap:12px;align-items:center;margin-right:60px}}
.mh-pill span.date {{ color: #e5e7eb; }}
.mh-pill span.sid {{ color: #a855f7; border-left: 1px solid rgba(255,255,255,0.2); padding-left: 12px; pointer-events: auto !important; user-select: all !important; position: relative; z-index: 9999 !important; }}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;background:#4ade80;box-shadow:0 0 8px #4ade80;margin-right:0px}}

[data-testid="stChatMessage"]{{box-sizing:border-box;max-width:100%;min-width:0;overflow-wrap:anywhere;
  background:rgba(255,255,255,.05);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:14px 18px}}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){{
  background:linear-gradient(135deg,#6366f1,#9411CB);border:none;flex-direction:row-reverse;
  width:min(80%, 100%); margin-left:auto}}
[data-testid="stExpander"]{{background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.1);border-radius:12px;max-width:100%}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {{color:#d1d5db !important}}

/* bottom bar */
[data-testid="stBottom"],
[data-testid="stBottom"] > div {{
  position: absolute !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: var(--bar) !important;
  width: 100% !important;
  z-index: 100 !important;
  background: #000 !important;
  transform: none !important;
}}
[data-testid="stBottomBlockContainer"]{{background:transparent !important}}
[data-testid="stBottomBlockContainer"]{{max-width:1100px;box-sizing:border-box;padding:12px 16px 20px 16px;margin: 0 auto;overflow-x:hidden}}
[data-testid="stChatInput"], [data-testid="stChatInput"] > div{{background:rgba(0,0,0,.6) !important;border-radius:16px}}
[data-testid="stChatInput"]{{border:1px solid rgba(255,255,255,.2);box-shadow:0 0 24px rgba(148,17,203,.25);min-width:0}}
[data-testid="stChatInput"] textarea{{color:#fff !important;background:transparent !important}}
[data-testid="stChatInput"] textarea::placeholder{{color:#9ca3af !important}}
[data-testid="stBottom"] .stButton button{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);
  color:#e5e7eb;border-radius:12px;white-space:nowrap}}
[data-testid="stBottom"] .stButton button:hover{{background:rgba(239,68,68,.35);border-color:#f87171;color:#fff}}
[data-testid="stToggle"] label p{{color:#e5e7eb !important;white-space:nowrap}}

/* Avatars */
[data-testid="stChatMessageAvatarUser"] {{ background: transparent !important; }}

/* Debug Panel */
.st-key-debug_panel_container {{
    position: fixed;
    right: 0;
    top: var(--hdr);
    width: 40vw;
    height: calc(100vh - var(--hdr));
    overflow-y: auto;
    padding: 20px 20px 100px 20px;
    background: #09090b;
    border-left: 1px solid rgba(255,255,255,0.1);
    z-index: 90;
}}
.st-key-debug_panel_container [data-testid="stExpander"] [data-testid="stVerticalBlock"] {{
  max-height: 400px;
  overflow-y: auto;
}}
/* --- Mobile Responsiveness Media Queries --- */
@media (min-width: 769px) {{
  /* On desktop, hide the mobile versions in the popover */
  .st-key-show_debug_mobile, .st-key-new_chat_mobile, .mh-pill-mobile {{ display: none !important; }}
}}
@media (max-width: 768px) {{
  /* On mobile, hide the desktop versions */
  .mh-pill {{ display: none !important; }}
  .st-key-show_debug, .st-key-new_chat {{ display: none !important; }}
  
  /* On mobile, show the mobile versions in the popover */
  .st-key-show_debug_mobile, .st-key-new_chat_mobile {{ display: block !important; }}
  .mh-pill-mobile {{ 
    pointer-events: auto; padding: 8px 18px; border-radius: 999px; 
    background: rgba(0,0,0,0.9); border: 1px solid rgba(255,255,255,0.1);
    font-size: 0.7rem; font-weight: 800; letter-spacing: 0.12em; 
    text-transform: uppercase; color: #fff; white-space: nowrap; 
    display: flex; gap: 12px; align-items: center; margin-bottom: 12px; justify-content: center;
  }}
  .mh-pill-mobile span.date {{ color: #e5e7eb; }}
  .mh-pill-mobile span.sid {{ color: #a855f7; border-left: 1px solid rgba(255,255,255,0.2); padding-left: 12px; }}
  
  /* On mobile, expand the input bar to take full width */
  [data-testid="stChatInput"] {{ width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }}
}}
</style>
"""

def inject_theme(sid: str = ""):
    # Inject blobs and header
    today = datetime.date.today().strftime("%d %B %Y")
    header_html = f"""
<div class="blob b1"></div><div class="blob b2"></div>
<div class="mh-header">
    <h1>Mehman Mira</h1>
    <div class="mh-pill">
        <span class="dot"></span>
        <span class="date">{today}</span>
        <span class="sid" data-sid="{sid}" style="cursor: pointer; user-select: all;" title="Click to copy">SID: {sid} 📋</span>
    </div>
</div>
"""
    st.markdown(CSS + header_html, unsafe_allow_html=True)
    import streamlit.components.v1 as components
    components.html(f"""
    <script>
        if (!window.parent.mhClipboardInit) {{
            window.parent.mhClipboardInit = true;
            
            // Try window.parent.document first
            const targetDoc = window.parent.document;
            
            targetDoc.addEventListener('click', function(e) {{
                if (e.target && e.target.matches('.mh-pill span.sid')) {{
                    const sidText = e.target.getAttribute('data-sid');
                    if (!sidText) return;
                    
                    navigator.clipboard.writeText(sidText).then(() => {{
                        const originalText = e.target.innerHTML;
                        if (!originalText.includes('✅')) {{
                            e.target.innerHTML = "SID: " + sidText + " ✅";
                            setTimeout(() => e.target.innerHTML = originalText, 1000);
                        }}
                    }}).catch(err => {{
                        const tempInput = targetDoc.createElement('input');
                        tempInput.value = sidText;
                        targetDoc.body.appendChild(tempInput);
                        tempInput.select();
                        targetDoc.execCommand('copy');
                        targetDoc.body.removeChild(tempInput);
                        
                        const originalText = e.target.innerHTML;
                        if (!originalText.includes('✅')) {{
                            e.target.innerHTML = "SID: " + sidText + " ✅";
                            setTimeout(() => e.target.innerHTML = originalText, 1000);
                        }}
                    }});
                }}
            }});
        }}
    </script>
    """, height=0, width=0)

def render_empty_state():
    st.markdown("""
    ## Welcome to Mehman Mira
    I am your AI hotel-booking assistant, ready to help you find the perfect stay.
    
    You can try asking me things like:
    - *I'm looking for a private place in Goa this weekend for 3 people.*
    - *Can you find me something under ₹10,000 per night?*
    - *Book me the Sea View Villa.*
    """)
