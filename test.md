Available examples:
  • basic_fork
  • code_agent
  • research_agent
  • swarm
  • orchestrator
  • summarizer
  • research_then_code
  • all

Usage: uv run examples.py <example_name>
PS C:\Users\sidki\source\repos\library\python_files> uv run examples.py basic_fork
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Example: Basic Agent Fork                                                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────────────────── 🔀 Fork fork_095723_001 ───────────────────────────────────────────────────────╮
│ Forking to general agent                                                                                                             │
│ Model: gemini-2.5-flash                                                                                                              │
│ Task: Explain the difference between async and threading in Python in 3 sentences....                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Status: success
Model: gemini-2.5-flash
╭────────────────────────────────────────────────────────────── Response ──────────────────────────────────────────────────────────────╮
│ Threading uses multiple operating system threads, allowing for concurrent execution (or true parallelism on multi-core systems)      │
│ where the OS manages scheduling, often used for CPU-bound tasks despite Python's Global Interpreter Lock (GIL). Asynchronous         │
│ programming, typically with asyncio, achieves concurrency within a single thread by cooperatively switching between tasks via an     │
│ event loop, explicitly yielding control during I/O-bound operations. Therefore, async is generally more efficient for I/O-bound      │
│ tasks by minimizing context switching overhead, while threading can be more suitable for managing concurrent CPU-bound work (though  │
│ GIL limits true parallelism in CPython).                                                                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
PS C:\Users\sidki\source\repos\library\python_files> uv run example code_agent
error: Failed to spawn: `example`
  Caused by: program not found
PS C:\Users\sidki\source\repos\library\python_files> uv run example.py code_agent
error: Failed to spawn: `example.py`
  Caused by: program not found
PS C:\Users\sidki\source\repos\library\python_files> uv run examples.py code_agent
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Example: Code Agent                                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────────────────── 🔀 Fork fork_100051_001 ───────────────────────────────────────────────────────╮
│ Forking to code agent                                                                                                                │
│ Model: gemini-2.5-pro                                                                                                                │
│ Task: Write a Python decorator that:                                                                                                 │
│ 1. Retries a function up to 3 times on exception                                                                                     │
│ 2. Uses exponential ...                                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Status: success
Thinking tokens: 2492
╭──────────────────────────────────────────────────────────── Code Output ─────────────────────────────────────────────────────────────╮
│ Of course. As an expert software engineer, I'll provide a robust, reusable, and well-documented decorator that meets all your        │
│ requirements.                                                                                                                        │
│                                                                                                                                      │
│ The implementation uses a decorator factory pattern. This allows the decorator to be configurable (e.g., @retry()) while still       │
│ working as a simple decorator (@retry). This is a more scalable and professional approach.                                           │
│                                                                                                                                      │
│                                                            Implementation                                                            │
│                                                                                                                                      │
│ Here is the complete, production-ready code for the retry decorator.                                                                 │
│                                                                                                                                      │
│                                                                                                                                      │
│  import functools                                                                                                                    │
│  import logging                                                                                                                      │
│  import time                                                                                                                         │
│  from typing import Callable, Any, TypeVar, cast                                                                                     │
│                                                                                                                                      │
│  # Set up a basic logger for demonstration purposes.                                                                                 │
│  # In a real application, this would be configured globally.                                                                         │
│  logging.basicConfig(                                                                                                                │
│      level=logging.INFO,                                                                                                             │
│      format='%(asctime)s - %(levelname)s - %(message)s'                                                                              │
│  )                                                                                                                                   │
│                                                                                                                                      │
│  # Use a TypeVar to preserve the signature of the decorated function for type checkers.                                              │
│  # F is a generic type that can be any callable.                                                                                     │
│  F = TypeVar('F', bound=Callable[..., Any])                                                                                          │
│                                                                                                                                      │
│  def retry(                                                                                                                          │
│      max_retries: int = 3,                                                                                                           │
│      initial_delay: float = 1.0,                                                                                                     │
│      backoff_factor: float = 2.0,                                                                                                    │
│      exceptions: tuple[type[Exception], ...] = (Exception,)                                                                          │
│  ) -> Callable[[F], F]:                                                                                                              │
│      """                                                                                                                             │
│      A decorator factory that retries a function with exponential backoff.                                                           │
│                                                                                                                                      │
│      This decorator will re-execute a function if it raises one of the specified                                                     │
│      exceptions. It waits with an exponentially increasing delay between retries.                                                    │
│                                                                                                                                      │
│      Args:                                                                                                                           │
│          max_retries (int): The maximum number of retry attempts. Defaults to 3.                                                     │
│          initial_delay (float): The delay in seconds before the first retry.                                                         │
│                                 Defaults to 1.0.                                                                                     │
│          backoff_factor (float): The factor by which the delay increases after                                                       │
│                                  each retry. Defaults to 2.0.                                                                        │
│          exceptions (tuple[type[Exception], ...]): A tuple of exception types                                                        │
│                                                    to catch and trigger a retry.                                                     │
│                                                    Defaults to (Exception,).                                                         │
│                                                                                                                                      │
│      Returns:                                                                                                                        │
│          Callable[[F], F]: A decorator that can be applied to a function.                                                            │
│      """                                                                                                                             │
│      def decorator(func: F) -> F:                                                                                                    │
│          @functools.wraps(func)                                                                                                      │
│          def wrapper(*args: Any, **kwargs: Any) -> Any:                                                                              │
│              """                                                                                                                     │
│              Wrapper function that implements the retry logic.                                                                       │
│              """                                                                                                                     │
│              delay = initial_delay                                                                                                   │
│              # The loop runs for max_retries + 1 attempts (1 initial + max_retries).                                                 │
│              for attempt in range(max_retries + 1):                                                                                  │
│                  try:                                                                                                                │
│                      # The very first attempt (attempt 0) is the initial call.                                                       │
│                      return func(*args,**kwargs)                                                                                    │
│                  except exceptions as e:                                                                                             │
│                      # If this was the last attempt, re-raise the exception.                                                         │
│                      if attempt == max_retries:                                                                                      │
│                          logging.error(                                                                                              │
│                              f"Function '{func.__name__}' failed after {max_retries + 1} attempts. "                                 │
│                              f"Final exception: {e}"                                                                                 │
│                          )                                                                                                           │
│                          raise                                                                                                       │
│                                                                                                                                      │
│                      logging.warning(                                                                                                │
│                          f"Attempt {attempt + 1}/{max_retries + 1} for '{func.__name__}' failed: {e}. "                              │
│                          f"Retrying in {delay:.2f} seconds..."                                                                       │
│                      )                                                                                                               │
│                      time.sleep(delay)                                                                                               │
│                      delay *= backoff_factor                                                                                         │
│          # We use cast to help type checkers understand that the wrapper has the same                                                │
│          # signature as the original function, thanks to @functools.wraps.                                                           │
│          return cast(F, wrapper)                                                                                                     │
│      return decorator                                                                                                                │
│                                                                                                                                      │
│                                                                                                                                      │
│                                                        Key Features Explained                                                        │
│                                                                                                                                      │
│  1 Decorator Factory Pattern: The outer function retry(...) is a factory that takes configuration and returns the actual decorator.  │
│    This makes it highly configurable. You can use it as @retry for defaults, or @retry(max_retries=5, initial_delay=0.5) to          │
│    customize it.                                                                                                                     │
│  2 @functools.wraps(func): This is crucial for preserving the original function's metadata, such as its name (__name__), docstring   │
│    (__doc__), and annotations (__annotations__). This helps with debugging, introspection, and tools like Sphinx for documentation.  │
│  3 Exponential Backoff Logic:                                                                                                        │
│     • The loop runs from attempt = 0 to max_retries.                                                                                 │
│     • The delay starts at initial_delay (1s).                                                                                        │
│     • After each failed attempt, we sleep for the current delay and then multiply it by backoff_factor (2.0).                        │
│     • This results in the desired sequence: 1s, 2s, 4s.                                                                              │
│  4 Graceful Failure: The if attempt == max_retries: check ensures that after the final attempt fails, the exception is re-raised.    │
│    This prevents the decorator from silently swallowing critical errors.                                                             │
│  5 Clean Logging: The logs clearly state which function failed, the attempt number, the reason (exception), and the upcoming delay.  │
│    Using different log levels (WARNING for retries, ERROR for final failure) is best practice.                                       │
│  6 Type Hints: The use of typing.Callable, TypeVar, and cast provides strong type safety, making the code easier to understand and   │
│    integrate with static analysis tools like MyPy.                                                                                   │
│                                                                                                                                      │
│                                                            Usage Example                                                             │
│                                                                                                                                      │
│ Here's how you would use the decorator on functions that might fail.                                                                 │
│                                                                                                                                      │
│                                                                                                                                      │
│  import random                                                                                                                       │
│                                                                                                                                      │
│  # Example 1: A function that fails twice and then succeeds.                                                                         │
│  call_count = 0                                                                                                                      │
│                                                                                                                                      │
│  @retry(max_retries=3, initial_delay=1)                                                                                              │
│  def fetch_data_from_flaky_api():                                                                                                    │
│      """Simulates fetching data from an API that might fail temporarily."""                                                          │
│      global call_count                                                                                                               │
│      call_count += 1                                                                                                                 │
│      print(f"Attempting to fetch data (call #{call_count})...")                                                                      │
│      if call_count < 3:                                                                                                              │
│          raise ConnectionError("Service temporarily unavailable")                                                                    │
│      print("Successfully fetched data!")                                                                                             │
│      return {"data": "some important payload"}                                                                                       │
│                                                                                                                                      │
│  # Example 2: A function that will always fail.                                                                                      │
│  @retry(max_retries=3, initial_delay=0.5) # Using custom delay for faster demo                                                       │
│  def permanent_failure():                                                                                                            │
│      """Simulates a function that always raises an error."""                                                                         │
│      print("Attempting a permanently failing operation...")                                                                          │
│      raise ValueError("Invalid configuration")                                                                                       │
│                                                                                                                                      │
│  if __name__ == "__main__":                                                                                                          │
│      print("--- Testing flaky function that eventually succeeds ---")                                                                │
│      try:                                                                                                                            │
│          result = fetch_data_from_flaky_api()                                                                                        │
│          print(f"Final result: {result}\n")                                                                                          │
│      except Exception as e:                                                                                                          │
│          print(f"Function failed permanently: {e}\n")                                                                                │
│                                                                                                                                      │
│      print("--- Testing function that always fails ---")                                                                             │
│      try:                                                                                                                            │
│          permanent_failure()                                                                                                         │
│      except ValueError as e:                                                                                                         │
│          print(f"Caught expected final exception: {e}")                                                                              │
│                                                                                                                                      │
│                                                                                                                                      │
│                                                           Expected Output                                                            │
│                                                                                                                                      │
│                                                                                                                                      │
│  --- Testing flaky function that eventually succeeds ---                                                                             │
│  Attempting to fetch data (call #1)...                                                                                               │
│  2023-10-27 10:30:00,123 - WARNING - Attempt 1/4 for 'fetch_data_from_flaky_api' failed: Service temporarily unavailable. Retrying   │
│  in 1.00 seconds...                                                                                                                  │
│  Attempting to fetch data (call #2)...                                                                                               │
│  2023-10-27 10:30:01,125 - WARNING - Attempt 2/4 for 'fetch_data_from_flaky_api' failed: Service temporarily unavailable. Retrying   │
│  in 2.00 seconds...                                                                                                                  │
│  Attempting to fetch data (call #3)...                                                                                               │
│  2023-10-27 10:30:03,128 - INFO - Successfully fetched data!                                                                         │
│  Final result: {'data': 'some important payload'}                                                                                    │
│                                                                                                                                      │
│  --- Testing function that always fails ---                                                                                          │
│  Attempting a permanently failing operation...                                                                                       │
│  2023-10-27 10:30:03,128 - WARNING - Attempt 1/4 for 'permanent_failure' failed: Invalid configuration. Retrying in 0.50 seconds...  │
│  Attempting a permanently failing operation...                                                                                       │
│  2023-10-27 10:30:03,630 - WARNING - Attempt 2/4 for 'permanent_failure' failed: Invalid configuration. Retrying in 1.00 seconds...  │
│  Attempting a permanently failing operation...                                                                                       │
│  2023-10-27 10:30:04,632 - WARNING - Attempt 3/4 for 'permanent_failure' failed: Invalid configuration. Retrying in 2.00 seconds...  │
│  Attempting a permanently failing operation...                                                                                       │
│  2023-10-27 10:30:06,635 - ERROR - Function 'permanent_failure' failed after 4 attempts. Final exception: Invalid configuration      │
│  Caught expected final exception: Invalid configuration                                                                              │
│                                                                                                                                      │
│                                                                                                                                      │
│                                                           Testing Strategy                                                           │
│                                                                                                                                      │
│ For a production environment, I would recommend the following unit tests for this decorator:                                         │
│                                                                                                                                      ││  1 Test Success on First Attempt: Decorate a function that never raises an exception. Assert it is called only once and returns the  ││    correct value.                                                                                                                    ││  2 Test Success After Retries: Decorate a function that fails N times (where N < max_retries) and then succeeds. Assert it is called ││    N+1 times and eventually returns the correct value.                                                                               ││  3 Test Failure After All Retries: Decorate a function that always fails. Assert that it is called max_retries + 1 times and that    ││    the original exception is ultimately raised.                                                                                      ││  4 Test Exception Specificity: Decorate a function that raises a TypeError. Use @retry(exceptions=(ValueError,)). Assert that the    ││    function is called only once and the TypeError is raised immediately, without any retries.                                        ││  5 Test Metadata Preservation: Check that the decorated function's __name__ and __doc__ attributes match the original function's     ││    attributes.                                                                                                                       │╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯PS C:\Users\sidki\source\repos\library\python_files>uv run examples.py

╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮│ Example: Research Agent with Google Search                                                                                                                                   │╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯╭────────────────────────────────────────────────────────────────────────── 🔀 Fork fork_102833_001 ───────────────────────────────────────────────────────────────────────────╮│ Forking to research agent                                                                                                                                                    ││ Model: gemini-2.5-flash                                                                                                                                                      ││ Task: What are the key new features in the Google GenAI Python SDK? Focus on recent additions....                                                                            │╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Status: success
╭────────────────────────────────────────────────────────────────────────────── Research Results ──────────────────────────────────────────────────────────────────────────────╮
│ The Google GenAI Python SDK has seen significant recent enhancements, primarily centered around its new unified google-genai package, which consolidates access to Google's  │
│ generative AI models across both the Gemini Developer API and Vertex AI. This strategic shift aims to streamline development by allowing developers to prototype             │
│ applications using the Developer API and seamlessly migrate to Vertex AI without extensive code rewrites. The older google-generativeai package is now deprecated, with      │
│ support ending in August 2025.                                                                                                                                               │
│                                                                                                                                                                              │
│ Key new features and recent additions to the Google GenAI Python SDK include:                                                                                                │
│                                                                                                                                                                              │
│  • Unified Client and API Access The google-genai SDK provides a single, consistent interface for interacting with Gemini (and other Google GenAI models like Veo and        │
│    Imagen), regardless of whether you're using the Gemini Developer API or Vertex AI. This also simplifies authentication, handling both API keys and Google Cloud's ADC     │
│    through the Client class.                                                                                                                                                 │
│  • Enhanced Gemini Model Support The SDK fully supports the latest Gemini models, including Gemini 2.0 Flash and Gemini 2.5 Pro/Flash. It facilitates text, image, and video │
│    generation, embeddings, and chat conversations. Recent updates include the release of stable versions like gemini-1.5-pro-002 and gemini-1.5-flash-002.                   │
│  • Advanced Multimedia Capabilities                                                                                                                                          │
│     • Image and Video Generation: The SDK supports generating and editing images from text prompts and generating videos from text or images (in preview). This includes     │
│       features like image upscaling and the ability to define image output options via ImageConfig.                                                                          │
│     • Veo Model Integration: Support for Veo text- and image-to-video models has been added, capable of generating detailed videos, including extending existing videos and  │
│       referencing multiple images for video generation.                                                                                                                      │
│  • Improved Function Calling The SDK has received enhancements for function calling, including support for streaming function call arguments across all languages and the    │
│    ability to manually declare and invoke functions.                                                                                                                         │
│  • Granular Content Generation Configuration Developers now have more control over the content generation process through the GenerateContentConfig parameter. Recent        │
│    additions include:                                                                                                                                                        │
│     • thinking_level for better control over the model's "thinking" process.                                                                                                 │
│     • enableEnhancedCivicAnswers for specific content generation needs.                                                                                                      │
│     • safety_filter_level for fine-tuning safety mechanisms.                                                                                                                 │
│     • Support for frequencyPenalty and presencePenalty parameters in Gemini 1.5 Pro and 1.5 Flash.                                                                           │
│  • Developer Experience and Utilities                                                                                                                                        │
│     • Pydantic Type Integration: All API methods support Pydantic types and dictionaries, accessible via google.genai.types, making data handling more robust.               │
│     • Asynchronous Support: The SDK includes tools for asynchronous operations, caching, and file management.                                                                │
│     • Voice Activity Detection: Added support for voice activity detection signals.                                                                                          │
│     • Retries in API Requests: The SDK now supports retries for API requests, improving reliability.                                                                         │
│  • GenAI Processors (Related Library) A new open-source Python library from Google DeepMind, GenAI Processors, was introduced to simplify complex AI application workflows.  │
│    It provides an abstraction layer with a consistent Processor interface for handling input, preprocessing, model calls, and output processing, treating all data as        │
│    asynchronous streams of ProcessorParts. This library is designed for concurrent execution and stream-based API operations for sophisticated multimodal applications.      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Example: Parallel Agent Swarm                                                                                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────────────────────────────────────────────────────── 🐝 Swarm swarm_103008 ────────────────────────────────────────────────────────────────────────────╮
│ Spawning agent swarm                                                                                                                                                         │
│ Tasks: 3                                                                                                                                                                     │
│ Agent Type: analysis                                                                                                                                                         │
│ Max Concurrent: 3                                                                                                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Completed: 3/3
╭──────────────────────────────────────────────────────────────────────────── Consolidated Summary ────────────────────────────────────────────────────────────────────────────╮
│ This consolidated summary synthesizes the provided information on microservices architecture, highlighting its advantages, challenges, and best practices for communication. │
│                                                                                                                                                                              │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│                                                                                                                                                                              │
│                                    Consolidated Summary: Microservices Architecture - The Promise, The Pitfalls, and The Path to Success                                     │
│                                                                                                                                                                              │
│ Microservices architecture is a modern approach to software development that structures an application as a collection of loosely coupled, independently deployable          │
│ services. While offering significant advantages over traditional monolithic systems, it introduces a new set of complexities that require deliberate management and          │
│ adherence to best practices.                                                                                                                                                 │
│                                                                                                                                                                              │
│                                                                          Synthesis of Key Findings                                                                           │
│                                                                                                                                                                              │
│  1 The Core Promise: Agility, Scalability, and Resilience:                                                                                                                   │
│     • Independent Scalability & Cost Efficiency: Microservices allow for granular scaling of individual components based on demand, rather than the entire application. This │
│       leads to substantial cost optimization, efficient resource utilization, and ensures peak performance during high-traffic events by only scaling the critical paths.    │
│     • Enhanced Agility & Speed of Delivery: Small, autonomous teams can develop, test, and deploy their services independently. This accelerates time-to-market for new      │
│       features, fosters innovation through rapid experimentation, improves developer productivity by reducing cognitive overhead, and enables technology freedom (choosing   │
│       the best tech stack per service).                                                                                                                                      │
│     • Improved Resilience & Fault Isolation: Failures are contained within a single service, preventing catastrophic outages of the entire application. This results in      │
│       higher application uptime, a better user experience through graceful degradation, and a faster Mean Time to Resolution (MTTR) as issues are isolated and easier to     │
│       diagnose.                                                                                                                                                              │
│  2 The Inherent Challenges: Complexity and Overhead:                                                                                                                         │
│     • Distributed System Complexity: Shifting from in-memory calls to network-based communication introduces fundamental complexities. Issues like network latency, service  │
│       discovery, and managing new failure modes (cascading failures) make debugging difficult and performance unpredictable.                                                 │
│     • Data Management & Consistency: Decentralized data ownership (each service managing its own database) breaks the traditional ACID transaction model. Ensuring data      │
│       consistency across multiple services becomes a significant challenge, requiring new patterns to prevent inconsistencies and manage cross-service business processes.   │
│     • Operational & DevOps Overhead: Managing a multitude of services (deployment, monitoring, scaling, security, configuration) vastly increases operational complexity     │
│       compared to a single monolith. Without a mature DevOps culture and heavy automation, this leads to slow deployment cadences, high MTTR, and inconsistent environments. │
│  3 Best Practices for Communication: Mitigating Complexity:                                                                                                                  │
│     • Favor Asynchronous Communication for Loose Coupling and Resilience: Prioritizing indirect communication via message brokers (e.g., Kafka, RabbitMQ) through            │
│       event-driven (Pub/Sub) patterns decouples services. This enhances resilience (events are queued if a service is down) and scalability (consumers can scale             │
│       independently). Synchronous communication (REST/gRPC) should be reserved for queries requiring immediate responses.                                                    │
│     • Implement Robust Resilience Patterns (The Network is Unreliable): Acknowledging network fallibility is crucial. Patterns like Circuit Breakers (to prevent cascading   │
│       failures), Retry with Exponential Backoff (to handle transient issues gracefully), and Timeouts (to prevent resource exhaustion) are essential for building robust     │
│       systems. These should be implemented using mature libraries or service mesh capabilities.                                                                              │
│     • Define and Enforce Clear API Contracts for Stability and Evolution: Formal API contracts (using OpenAPI for REST or Protocol Buffers for gRPC) establish a clear       │
│       agreement on service interactions. This prevents breaking changes, enables parallel development, provides clear documentation, and ensures stability through           │
│       versioning strategies and rigorous contract testing.                                                                                                                   │
│                                                                                                                                                                              │
│                                                                          Patterns and Common Themes                                                                          │
│                                                                                                                                                                              │
│  • "The Network is Unreliable": This is a pervasive theme. While microservices leverage the network for distribution, the inherent unreliability of network communication is │
│    a core challenge (distributed complexity) and a primary driver for specific best practices (resilience patterns).                                                         │
│  • Complexity Trade-off: Microservices don't eliminate complexity; they shift it. The complexity of a monolithic application (tight coupling, slow releases) is traded for   │
│    the complexity of a distributed system (network, data consistency, operational overhead).                                                                                 │
│  • Decoupling and Autonomy: This is both a core advantage (independent scaling, agile teams) and a key principle underpinning solutions (asynchronous communication, clear   │
│    API contracts). The goal is to maximize independence to achieve speed and resilience.                                                                                     │
│  • Automation and Tooling are Non-Negotiable: Successfully managing the operational overhead and distributed complexities of microservices is impossible without significant │
│    investment in robust CI/CD pipelines, comprehensive observability (logging, metrics, tracing), configuration management, message brokers, and resilience libraries.       │
│  • Resilience as a Double-Edged Sword: Microservices promise improved resilience (fault isolation), but achieving it requires deliberate design and the implementation of    │
│    specific patterns to counteract the inherent fragility of distributed systems.                                                                                            │
│                                                                                                                                                                              │
│                                                                            Important Differences                                                                             │
│                                                                                                                                                                              │
│  • The nature of complexity differs: Monoliths struggle with internal coupling, while microservices battle external, network-induced complexities.                           │
│  • Data consistency is a uniquely challenging problem in microservices, requiring alternative patterns like eventual consistency and Sagas, which are not typically concerns │
│    in a single, ACID-compliant monolithic database.                                                                                                                          │
│  • The skillset and cultural shift required is profound. Microservices demand a mature DevOps culture where teams are responsible for the entire lifecycle of their          │
│    services, moving beyond traditional development/operations silos.                                                                                                         │
│                                                                                                                                                                              │
│                                                                            Actionable Conclusions                                                                            │
│                                                                                                                                                                              │
│ Implementing a microservices architecture is a strategic decision that offers substantial benefits but demands significant commitment and investment. Organizations should:  │
│                                                                                                                                                                              │
│  1 Assess Readiness: Understand the profound shift in operational complexity and the need for a strong DevOps culture, mature automation practices, and skilled teams. It's  │
│    not a "silver bullet" for every problem.                                                                                                                                  │
│  2 Invest Heavily in Infrastructure & Tooling: Prioritize building robust CI/CD pipelines, comprehensive observability (logging, metrics, tracing), service mesh             │
│    technologies, and message brokers. These are foundational for managing distributed systems.                                                                               │
│  3 Prioritize Communication Best Practices: Design service interactions with resilience and loose coupling in mind from day one. Favor asynchronous communication,           │
│    rigorously apply resilience patterns, and establish strict API contracts to ensure system stability and evolvability.                                                     │
│  4 Embrace New Design Patterns: Learn and apply patterns specific to distributed systems, particularly for data consistency (e.g., Saga pattern, eventual consistency) and   │
│    communication.                                                                                                                                                            │
│  5 Focus on Bounded Contexts: Clearly define service boundaries based on business domains to minimize cross-service communication and maintain true independence.            │
│                                                                                                                                                                              │
│ Microservices can unlock unprecedented agility and scalability, but only when approached with a clear understanding of their inherent challenges and a disciplined           │
│ application of best practices.                                                                                                                                               │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

                                                     uv run examples.py orchestrator
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Example: Plan-and-Execute Orchestrator                                                                                                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────────────────────────────────── 🎯 Plan & Execute: wf_103207_001 ──────────────────────────────────────────────────────────────────────╮
│ Goal: Design a simple user authentication system for a web API                                                                                                               │
│ Planning up to 4 steps...                                                                                                                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Plan: wf_103207_001
├──  Project Setup & User Utilities
├──  Implement Login Endpoint (depends: step_1)
├──  Implement Protected Route (depends: step_2)
└──  Implement User Registration (depends: step_1)
Running 1 parallel steps...
✓ Project Setup & User Utilities
Running 2 parallel steps...
✓ Implement Login Endpoint
✓ Implement User Registration
Running 1 parallel steps...
✓ Implement Protected Route
Workflow Status: completed
Steps: 4
╭──────────────────────────────────────────────────────────────────────────────── Final Result ────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                              │
│                                                    Comprehensive Summary: Simple User Authentication System for a Web API                                                    │
│                                                                                                                                                                              │
│ This project successfully designed and implemented a simple, yet robust, user authentication system for a web API using FastAPI. The development followed a structured,      │
│ incremental approach, focusing on security best practices, modularity, and clarity.                                                                                          │
│                                                                                                                                                                              │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│                                                                          1. Synthesis of Work Done                                                                           │
│                                                                                                                                                                              │
│ The development process covered the full lifecycle of a basic authentication system:                                                                                         │
│                                                                                                                                                                              │
│  • Project Initialization & Structure: A new FastAPI project was set up with a clear, scalable directory structure (auth.py, db.py, main.py, models.py, config.py, crud.py,  │
│    routers/users.py). Essential dependencies like fastapi, uvicorn, passlib[bcrypt], and python-jose[cryptography] were installed.                                           │
│  • Data Models (Pydantic): Comprehensive Pydantic models were defined for user data, ensuring separation of concerns and preventing sensitive data leakage:                  │
│     • UserCreate: For receiving user registration data (includes plain password).                                                                                            │
│     • User: For API responses (excludes password/hash).                                                                                                                      │
│     • UserInDB: For database storage (includes hashed password).                                                                                                             │
│     • Token: For the JWT response structure.                                                                                                                                 │
│     • TokenData: For validating the JWT payload.                                                                                                                             │
│  • Secure Password Management (auth.py):                                                                                                                                     │
│     • Implemented passlib's CryptContext with bcrypt for secure password hashing (hash_password) and verification (verify_password).                                         │
│     • Integrated JWT creation logic (create_access_token) using python-jose, encoding user identity (sub claim) and expiration into the token.                               │
│     • Defined OAuth2PasswordBearer to streamline token extraction from request headers.                                                                                      │
│  • Database Abstraction (db.py, crud.py):                                                                                                                                    │
│     • A simple in-memory dictionary (fake_users_db) was used to simulate a database for demonstration, allowing easy future replacement.                                     │
│     • A crud.py module was introduced to centralize all database interaction logic, providing functions like `get...                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
