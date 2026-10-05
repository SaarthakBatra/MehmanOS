import os
import uuid
import streamlit as st
from pydantic import ValidationError

from agent.config.src.config import get_settings
from agent.orchestrator.src.orchestrator import process_turn, TurnResult
from agent.state.src.state import BookingContext, context_to_dict
from agent.tools.booking.src.booking import admin_reset_database
from agent.session_store.src.session_store import load_context, delete_context

from ui.app.src.view_model import strip_state_updates, summarize_state, summarize_trace
from ui.app.src.theme import inject_theme, render_empty_state


# Setup the main Streamlit page configuration
st.set_page_config(
    page_title="Mehman Mira", 
    page_icon="🏨", 
    layout="wide",
    initial_sidebar_state="collapsed"
)


def reconstruct_ui_history(context: BookingContext) -> list:
    from ui.app.src.view_model import strip_state_updates
    import json
    
    ui_history = []
    if not hasattr(context, "conversation_history") or not context.conversation_history:
        return ui_history
        
    current_steps = []
    pending_calls = {}
    
    for item in context.conversation_history:
        role = ""
        parts = []
        if isinstance(item, dict):
            role = item.get("role", "user")
            parts = item.get("parts", [])
        else:
            role = getattr(item, "role", "user")
            parts = getattr(item, "parts", [])
            
        for p in parts:
            if isinstance(p, dict):
                if "function_call" in p:
                    fc = p["function_call"]
                    fc_id = fc.get("id", str(len(current_steps)))
                    step = {
                        "tool_call_id": fc_id,
                        "tool_name": fc.get("name", ""),
                        "tool_args": fc.get("args", {})
                    }
                    pending_calls[fc_id] = step
                    current_steps.append(step)
                elif "function_response" in p:
                    fr = p["function_response"]
                    fr_id = fr.get("id")
                    if fr_id in pending_calls:
                        res_data = fr.get("response", {})
                        pending_calls[fr_id]["tool_result"] = json.dumps(res_data) if isinstance(res_data, dict) else str(res_data)
                elif "text" in p:
                    text = strip_state_updates(p.get("text", ""))
                    if text.strip():
                        ui_history.append({"role": "assistant" if role == "model" else role, "content": text, "steps": current_steps.copy() if role == "model" else []})
                        if role == "model":
                            current_steps = []
                            pending_calls = {}
            else:
                if hasattr(p, "function_call") and p.function_call:
                    fc = p.function_call
                    fc_id = getattr(fc, "id", str(len(current_steps)))
                    args = getattr(fc, "args", {})
                    step = {
                        "tool_call_id": fc_id,
                        "tool_name": getattr(fc, "name", ""),
                        "tool_args": args
                    }
                    pending_calls[fc_id] = step
                    current_steps.append(step)
                elif hasattr(p, "function_response") and p.function_response:
                    fr = p.function_response
                    fr_id = getattr(fr, "id", None)
                    if fr_id in pending_calls:
                        res_data = getattr(fr, "response", {})
                        pending_calls[fr_id]["tool_result"] = json.dumps(res_data) if isinstance(res_data, dict) else str(res_data)
                elif hasattr(p, "text") and p.text:
                    text = strip_state_updates(p.text)
                    if text.strip():
                        ui_history.append({"role": "assistant" if role == "model" else role, "content": text, "steps": current_steps.copy() if role == "model" else []})
                        if role == "model":
                            current_steps = []
                            pending_calls = {}
                            
    # Fallback to context.tool_traces for the last turn if steps got missed
    if ui_history and hasattr(context, "tool_traces") and context.tool_traces:
        last_msg = None
        for msg in reversed(ui_history):
            if msg["role"] == "assistant":
                last_msg = msg
                break
        if last_msg and not last_msg.get("steps"):
            last_msg["steps"] = context.tool_traces
            
    return ui_history


def init_session() -> None:
    query_params = st.query_params
    
    if "sid" not in query_params and "sid" not in st.session_state:
        new_sid = uuid.uuid4().hex[:12]
        st.query_params["sid"] = new_sid
        st.session_state.sid = new_sid
        st.session_state.booking_context = BookingContext()
        st.session_state.history = [{"role": "assistant", "content": "Welcome to Mehman! I am Mira, your hotel booking assistant. How can I help you today?", "steps": []}]
        st.session_state.show_debug = False
        return
        
    current_sid = query_params.get("sid", st.session_state.get("sid"))
    
    if not (isinstance(current_sid, str) and len(current_sid) == 12 and all(c in "0123456789abcdef" for c in current_sid)):
        st.error("Invalid session ID. Please start a new chat.")
        if st.button("Start New Chat", type="primary", key="bad_sid_new"):
            st.query_params.clear()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.stop()
    
    if "sid" not in st.session_state or st.session_state.sid != current_sid:
        st.session_state.sid = current_sid
        st.query_params["sid"] = current_sid
        st.session_state.show_debug = False
        
        try:
            context = load_context(current_sid)
            st.session_state.booking_context = context
            history = reconstruct_ui_history(context)
            if history:
                if history[0]["content"] != "Welcome to Mehman! I am Mira, your hotel booking assistant. How can I help you today?":
                    history.insert(0, {"role": "assistant", "content": "Welcome to Mehman! I am Mira, your hotel booking assistant. How can I help you today?", "steps": []})
                st.session_state.history = history
            else:
                st.session_state.history = [{"role": "assistant", "content": "Welcome to Mehman! I am Mira, your hotel booking assistant. How can I help you today?", "steps": []}]
        except Exception:
            st.error("Failed to load session or session does not exist. Please start a new chat.")
            if st.button("Start New Chat", type="primary", key="load_fail_new"):
                st.query_params.clear()
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            st.stop()


def clear_db():
    success = admin_reset_database()
    if success:
        if hasattr(st.session_state, "sid"):
            try:
                delete_context(st.session_state.sid)
            except Exception:
                pass
    return success

@st.dialog("Clear Database")
def clear_db_dialog():
    st.warning("This will permanently delete the current session and wipe the entire backend database.")
    confirmation = st.text_input('Type "CONFIRM" to proceed:')
    if st.button("Delete Database", type="primary", disabled=(confirmation != "CONFIRM")):
        success = clear_db()
        if success:
            st.success("Database cleared successfully.")
            import time; time.sleep(1.5)
            st.rerun()
        else:
            st.error("Failed to clear database.")


@st.dialog("Start New Chat")
def new_chat_dialog():
    st.write("Are you sure you want to start a new chat? Your current session will be saved.")
    if st.button("Start New Chat", type="primary"):
        new_sid = uuid.uuid4().hex[:12]
        st.query_params["sid"] = new_sid
        st.session_state.sid = new_sid
        st.session_state.booking_context = BookingContext()
        st.session_state.history = [{"role": "assistant", "content": "Welcome to Mehman Mira! How can I help you book your stay?", "steps": []}]
        st.rerun()


@st.dialog("Load Chat")
def load_chat_dialog():
    st.write("Enter an existing Session ID (SID) to load:")
    sid_input = st.text_input("SID:")
    if st.button("Load Chat", type="primary"):
        if sid_input:
            st.query_params["sid"] = sid_input
            if "sid" in st.session_state:
                del st.session_state["sid"]
            st.rerun()


def main() -> None:
    try:
        get_settings.cache_clear()
        get_settings()
    except ValidationError:
        st.error("Missing GOOGLE_API_KEY. Please set it in .env.")
        st.stop()
        
    init_session()
    inject_theme(st.session_state.sid)
    
    # Top Right Menu
    with st.container(key="top_right_menu"):
        with st.popover(":material/settings:", use_container_width=False):
            if st.button("Load Chat"):
                load_chat_dialog()
            if st.button("Clear Database"):
                clear_db_dialog()
    
    # Render bottom bar first
    prompt = None
    with st.bottom:
        with st.container(horizontal=True, vertical_alignment="center"):
            prompt = st.chat_input("Type your message here...")
            st.toggle("Debug View", key="show_debug")
            if st.button("New Chat", key="new_chat"):
                new_chat_dialog()

    # Layout logic: split screen if debug is shown
    if st.session_state.get("show_debug", False):
        chat_col, debug_col = st.columns([6, 4])
    else:
        chat_col = st.container()
        debug_col = None

    # Main chat panel
    with chat_col:
        with st.container(key="chat_scroll"):
            with st.container(key="chat_inner"):
                    
                    # Show empty state only if there's no history beyond welcome AND no prompt
                    if len(st.session_state.history) <= 1 and not prompt:
                        render_empty_state()
                    
                    # Render all past history
                    for msg in st.session_state.history:
                        import os
                        avatar_path = os.path.join(os.path.dirname(__file__), "assets/mira_avatar.jpg")
                        avatar = avatar_path if msg["role"] == "assistant" else None
                        with st.chat_message(msg["role"], avatar=avatar):
                            if msg.get("is_error"):
                                st.error(msg["content"])
                            st.markdown(msg["content"])
                                
                            # If there are agent steps, show them beautifully
                            if msg.get("steps") and len(msg["steps"]) > 0:
                                step_names = " → ".join([f"`{t.get('tool_name', 'tool')}`" for t in msg["steps"]])
                                with st.expander(f"Agent Steps: {step_names}"):
                                    steps_list = msg["steps"]
                                    for i in range(0, len(steps_list), 3):
                                        row_steps = steps_list[i:i+3]
                                        cols = st.columns(len(row_steps))
                                        for c_idx, col in enumerate(cols):
                                            with col:
                                                step = summarize_trace(row_steps[c_idx])
                                                icon = "✅" if step["ok"] else "❌"
                                                with st.popover(f"{icon} {step['tool']}", use_container_width=True):
                                                    st.markdown("**Arguments:**")
                                                    args_dict = step.get('args', {})
                                                    if args_dict:
                                                        for k, v in args_dict.items():
                                                            st.markdown(f"- **{k}**: `{v}`")
                                                    else:
                                                        st.markdown("*None*")
                                                        
                                                    st.markdown("**Result:**")
                                                    res_dict = step.get('result', {})
                                                    if isinstance(res_dict, dict) and res_dict:
                                                        for k, v in res_dict.items():
                                                            if isinstance(v, list):
                                                                st.markdown(f"- **{k}**: {len(v)} items found")
                                                            elif isinstance(v, dict):
                                                                st.markdown(f"- **{k}**: (Complex object)")
                                                            else:
                                                                st.markdown(f"- **{k}**: `{v}`")
                                                    else:
                                                        st.markdown(str(res_dict))
                    
                    
                    st.markdown("<div id='chat-end'></div>", unsafe_allow_html=True)
                    current_history_len = len(st.session_state.history)
                    if st.session_state.get("last_history_len", 0) != current_history_len:
                        st.session_state.last_history_len = current_history_len
                        import time
                        import streamlit.components.v1 as components
                        components.html(f"""
                        <script>
                            // Force script execution on new messages: {time.time()}
                            const targetDoc = window.parent.document;
                            
                            function forceScroll() {{
                                const selectors = ['.stMain', '.stApp', '.stMainBlockContainer', 'main', 'body', 'html'];
                                selectors.forEach(sel => {{
                                    const els = targetDoc.querySelectorAll(sel);
                                    els.forEach(el => {{
                                        // Some browsers/Streamlit versions prefer scrollTop, some prefer scrollTo
                                        el.scrollTop = el.scrollHeight + 99999;
                                        if (el.scrollTo) {{
                                            el.scrollTo({{ top: el.scrollHeight + 99999, behavior: 'smooth' }});
                                        }}
                                    }});
                                }});
                            }}
                            
                            // Run immediately, then again slightly later to account for DOM reflows
                            setTimeout(forceScroll, 50);
                            setTimeout(forceScroll, 400);
                        </script>
                        """, height=0, width=0)
                    
                    # Handle new user input inline for smooth animation
                    if prompt:
                        # 1. Instantly append and render user message
                        st.session_state.history.append({"role": "user", "content": prompt, "steps": []})
                        with st.chat_message("user", avatar=None):
                            st.markdown(prompt)
                        
                        # Trigger scroll immediately before blocking for API
                        import time
                        import streamlit.components.v1 as components
                        components.html(f"""
                        <script>
                            const targetDoc = window.parent.document;
                            function forceScroll() {{
                                const selectors = ['.stMainBlockContainer', '.stMain', '.stApp', 'main', 'body', 'html'];
                                selectors.forEach(sel => {{
                                    const els = targetDoc.querySelectorAll(sel);
                                    els.forEach(el => {{
                                        el.scrollTop = el.scrollHeight + 99999;
                                        if (el.scrollTo) el.scrollTo({{ top: el.scrollHeight + 99999, behavior: 'smooth' }});
                                    }});
                                }});
                            }}
                            setTimeout(forceScroll, 10);
                            setTimeout(forceScroll, 150);
                        </script>
                        """, height=0, width=0)
                        
                        # 2. Open assistant bubble and trigger spinner
                        with st.chat_message("assistant", avatar="ui/app/src/assets/mira_avatar.jpg"):
                            with st.spinner("Thinking..."):
                                result: TurnResult = process_turn(st.session_state.sid, prompt)
                                
                                if result.is_error:
                                    st.session_state.history.append({
                                        "role": "assistant", 
                                        "content": result.response_text,
                                        "steps": [],
                                        "is_error": True
                                    })
                                else:
                                    st.session_state.booking_context = result.current_state
                                    cleaned_text = strip_state_updates(result.response_text)
                                    
                                    turn_traces = []
                                    if isinstance(result.current_state, dict):
                                        turn_traces = result.current_state.get("tool_traces", [])
                                    else:
                                        turn_traces = getattr(result.current_state, "tool_traces", [])
                                        
                                    st.session_state.history.append({
                                        "role": "assistant", 
                                        "content": cleaned_text,
                                        "steps": turn_traces
                                    })
                            
                            # Trigger a rerun so the final message (and debug panel) redraw fully
                            st.rerun()

    # Debug Panel Sidebar
    if st.session_state.get("show_debug", False) and debug_col is not None:
        with debug_col:
            with st.container(key="debug_panel_container"):
                st.subheader("Debug Panel")
                
                # Summarized Context
                ctx = st.session_state.booking_context
                summary = summarize_state(ctx)
                
                if summary:
                    for label, value in summary:
                        st.markdown(f"**{label}**: {value}")
                else:
                    st.markdown("*No active context.*")
                    
                st.markdown("---")
                
                # Raw state (collapsed)
                with st.expander("Raw State (Developer)"):
                    import json
                    import dataclasses
                    try:
                        if dataclasses.is_dataclass(ctx):
                            st.code(json.dumps(context_to_dict(ctx), indent=2), language="json")
                        elif hasattr(ctx, "__dict__"):
                            st.code(json.dumps(ctx.__dict__, default=str, indent=2), language="json")
                        else:
                            st.code(json.dumps(ctx, default=str, indent=2), language="json")
                    except Exception:
                        st.code(str(ctx))

if __name__ == "__main__":
    main()
