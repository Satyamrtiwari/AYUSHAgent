import asyncio
import sys

from .graph import build_graph


class LangGraphAYUSHPipeline:
    def __init__(self):
        self.graph = build_graph()

    def run(self, raw_text, patient_ref, auto_push=False):
        state = {
            "raw_text": raw_text,
            "patient_ref": patient_ref,
            "auto_push": auto_push
        }
        
        try:
            # Check if there's a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If loop is running, we need nest_asyncio
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    return loop.run_until_complete(self.graph.ainvoke(state))
                except ImportError:
                    # nest_asyncio not installed - use thread pool
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.graph.ainvoke(state))
                        return future.result(timeout=60)  # 60 second timeout
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(self.graph.ainvoke(state))
        except Exception as e:
            import traceback
            error_msg = f"Pipeline execution error: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            # Return error state instead of raising
            return {
                "error": error_msg,
                "ayush_term": raw_text[:50] if raw_text else "Unknown",
                "best": {"code": "UNK", "title": "Error"},
                "confidence": 0.0,
                "reason": f"Pipeline failed: {str(e)}",
                "needs_human_review": True
            }
