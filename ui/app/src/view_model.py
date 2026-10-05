import re

def strip_state_updates(text: str) -> str:
    """
    Strips <state_update>...</state_update> XML blocks from a string.
    
    This function removes all text contained within <state_update> tags, 
    including the tags themselves. This is primarily used to prevent 
    agent-directed state update blocks from being rendered in the UI.

    Args:
        text (str): The raw text response from the agent containing potential state updates.

    Returns:
        str: The cleaned text with all <state_update> blocks removed.
    """
    if not text:
        return text
        
    # Non-greedy regex substitution spanning multiple lines using re.DOTALL
    # Also handles hallucinated closing tags like <state_update>
    return re.sub(r'<state_update>.*?(?:</state_update>|<state_update>)', '', text, flags=re.DOTALL)


from typing import Dict, Any, List, Tuple
from agent.state.src.state import BookingContext, context_to_dict

def summarize_state(state: Any) -> List[Tuple[str, str]]:
    if not isinstance(state, dict):
        try:
            from dataclasses import asdict
            state = asdict(state)
        except Exception:
            state = getattr(state, "__dict__", {})
        
    summary = []
    
    # Destination
    if state.get("destination"):
        summary.append(("Destination", str(state["destination"])))
        
    # Dates
    check_in = state.get("check_in")
    check_out = state.get("check_out")
    
    def format_date(d: str) -> str:
        try:
            from datetime import date
            return date.fromisoformat(d).strftime("%d %b %Y")
        except Exception:
            return d

    if check_in and check_out:
        summary.append(("Dates", f"{format_date(check_in)} to {format_date(check_out)}"))
    elif check_in:
        summary.append(("Dates", f"From {format_date(check_in)}"))
        
    # Guests
    if state.get("guests"):
        summary.append(("Guests", str(state["guests"])))
        
    # Budget
    if state.get("budget_per_night"):
        try:
            budget = float(state["budget_per_night"])
            summary.append(("Budget", f"₹{int(budget):,}/night"))
        except (ValueError, TypeError):
            summary.append(("Budget", f"₹{state['budget_per_night']}/night"))
        
    # Room preference
    if state.get("room_preference"):
        summary.append(("Room preference", str(state["room_preference"])))
        
    # Selected property
    if state.get("selected_property_id"):
        summary.append(("Selected property", str(state["selected_property_id"])))
        
    # Selected room
    if state.get("selected_room_id"):
        summary.append(("Selected room", str(state["selected_room_id"])))
        
    # Add-ons
    if state.get("add_ons"):
        # Deduplicate while preserving order
        seen = set()
        deduped = [x for x in state["add_ons"] if not (x in seen or seen.add(x))]
        summary.append(("Add-ons", ", ".join(deduped)))
        
    # Booking hold ref
    if state.get("booking_hold_ref"):
        summary.append(("Booking hold ref", str(state["booking_hold_ref"])))
        
    # Next action
    if state.get("last_action"):
        summary.append(("Next action", str(state["last_action"])))
        
    return summary


def summarize_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
    tool = trace.get("tool_name", trace.get("tool", "unknown_tool"))
    
    # Args formatting
    args = {}
    tool_call = trace.get("tool_call")
    if isinstance(tool_call, dict) and "args" in tool_call:
        args = tool_call["args"]
    elif "tool_args" in trace:
        args = trace["tool_args"]
        
    # Filter out internal arguments (starting with _)
    if isinstance(args, dict):
        args = {k: v for k, v in args.items() if not str(k).startswith('_')}
    
    args_line = ", ".join(f"{str(k)}={str(v)}" for k, v in args.items()) if isinstance(args, dict) and args else ""
    if not args_line and not isinstance(tool_call, dict):
        args_line = str(tool_call)
        
    # Result formatting
    tool_result = trace.get("tool_result")
    
    import json
    if isinstance(tool_result, str):
        try:
            tool_result = json.loads(tool_result)
        except json.JSONDecodeError:
            pass
            
    is_error = False
    if isinstance(tool_result, dict) and "error" in tool_result:
        is_error = True
        
    result_line = ""
    
    if is_error:
        if isinstance(tool_result, dict):
            result_line = str(tool_result["error"])
        else:
            result_line = str(tool_result)
    else:
        if tool_result == "...[TRUNCATED]":
            result_line = "[TRUNCATED]"
        elif isinstance(tool_result, dict):
            if tool == "search_properties":
                matches = tool_result.get("matches", [])
                result_line = f"{len(matches)} matches"
            elif tool == "check_availability":
                available = tool_result.get("available", False)
                result_line = "available" if available else "unavailable"
            elif tool == "calculate_price":
                total = tool_result.get("total_price")
                result_line = f"₹{total}" if total else "price calculated"
            elif tool in ("get_property_details", "get_room_details"):
                result_line = tool_result.get("name", "details loaded")
            elif tool == "get_policy":
                policy = tool_result.get("policy", "")
                result_line = policy[:80] + "..." if len(policy) > 80 else policy
            elif tool == "create_booking_hold":
                ref = tool_result.get("booking_ref")
                result_line = f"Hold {ref}" if ref else "hold created"
            elif tool == "get_booking":
                ref = tool_result.get("booking_ref")
                result_line = f"Loaded {ref}" if ref else "booking loaded"
            elif tool == "cancel_booking":
                success = tool_result.get("success", False)
                result_line = "cancelled" if success else "cancel failed"
            else:
                result_line = str(tool_result)[:100]
        else:
            result_line = str(tool_result)[:100]
            
    return {
        "tool": tool,
        "args_line": args_line,
        "result_line": result_line,
        "ok": not is_error,
        "args": args,
        "result": tool_result if isinstance(tool_result, dict) else {"result": str(tool_result)}
    }
