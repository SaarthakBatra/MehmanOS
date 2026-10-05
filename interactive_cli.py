import uuid
import os
import sys

# Load environment variables (ensure python-dotenv is installed if not already)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import agent.orchestrator.src.orchestrator as orch

if not os.getenv('GOOGLE_API_KEY'):
    print('❌ ERROR: GOOGLE_API_KEY not found in environment.')
    sys.exit(1)

session_id = f'e2e_cli_test_{uuid.uuid4()}'

print('='*60)
print('🏨 Mira Interactive CLI (E2E Integration Test)')
print('Type \"exit\" or \"quit\" to end the session.')
print('='*60)
print(f'[Session ID: {session_id}]\n')

while True:
    try:
        user_input = input('You: ')
        if user_input.lower() in ['exit', 'quit']:
            print('\nEnding session. Goodbye!')
            break
            
        # Call the orchestrator
        result = orch.process_turn(session_id, user_input)
        
        # Display the response
        print(f'\nMira: {result.response_text}')
        
        # Log the underlying state for debugging purposes
        from agent.logger.src.logger import log_debug
        log_debug("DEBUG_STATE", result.current_state, session_id)
        
    except KeyboardInterrupt:
        print('\nEnding session. Goodbye!')
        break
    except Exception as e:
        print(f'\n[FATAL ERROR] {e}')
        break