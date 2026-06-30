# Week 5 - Review Questions

* What is the difference between AI, Machine Learning, and Generative AI, and how do these three terms relate to one another?
* Why does not all AI involve "learning"? Give an example of a rules-based AI system.
* What is a rules-based system good at, and what is its fundamental limitation?
* What is Machine Learning, and how does it differ from traditional rule-based programming?
* In machine learning, what does the human provide instead of writing the rules?
* What is training, and what are the parameters that result from it?
* What does generalization mean?
* What is the difference between supervised and unsupervised learning?
* What does it mean for training data to be "labeled," and which type of learning relies on it?
* What is the difference between the training phase and the prediction phase of a model?
* Why is writing hand-coded rules a poor approach for a problem like fraud detection?
* What is Generative AI, and how does it differ from models built to classify or predict?
* What does it mean for a model to be "generative"?
* Name three types of content that Generative AI can produce.
* At its heart, how does a generative model produce new content?
* What does it mean that a generative model is optimized to be "plausible" rather than "true"?
* How are rules-based AI, machine learning, and generative AI each used in a modern data stack? Give an example of each.
* What is a Large Language Model?
* What single task is an LLM fundamentally trained to do?
* What is a token, and roughly how much text does one represent?
* Describe the loop an LLM follows to generate a full response.
* What is the word "large" actually referring to in "Large Language Model"?
* What is a parameter in the context of an LLM, and why does scale matter?
* Why does an LLM's training data cutoff matter in daily use?
* What is a context window?
* At a high level, what distinguishes GPT, Claude, Gemini, Llama, and BERT from one another?
* What is the difference between a generative model and an "understanding" model like BERT? Give an example task for each.
* What is the difference between a closed model and an open-weight model, and why is it a data-control decision rather than a quality judgment?
* Name four realistic use cases for an LLM, and state the boundary or risk attached to each.
* What kinds of tasks do LLMs excel at, and what kinds do they struggle with?
* What does it mean that "you remain the source of truth" when using an LLM?
* What is prompt engineering, and why does it actually work given how an LLM generates text?
* Why can the same model produce very different outputs depending on how it is prompted?
* Name some characteristics of an effective prompt.
* What is zero-shot prompting, and when is it the right default?
* What is few-shot prompting, and what problem does it solve?
* How do worked examples in a few-shot prompt "condition" the model?
* What is the trade-off of adding more examples to a few-shot prompt?
* What is conditioning, and what are three ways to condition a model besides giving examples?
* Why does giving context rather than just a request produce better output? Give an example.
* Why is it useful to state constraints up front in a prompt?
* How does setting a role or audience change a model's output?
* Are LLM conversations stateful or stateless? Explain the behavior within a session versus across sessions.
* How does a model appear to "remember" earlier parts of a conversation?
* Why is it better to iterate on a close-but-wrong answer than to restart the conversation?
* Why can a very long conversation start to drift, and what is often the fix?
* Why must you mind the context window during a long session, and what should you do if something important was established far back?
* What is fine-tuning, and how does it differ from prompting?
* When is fine-tuning the appropriate tool rather than prompting?
* Summarize the trade-offs between prompting/conditioning and fine-tuning.
* What is a hallucination, and what root cause produces it?
* Why is a confident, well-formatted answer not evidence that it is correct?
* Why is verifying against authoritative sources the standard control for hallucination?
* Why is framing AI coding work as "pair programming" useful, and which role are you always in?
* How is using an AI coding tool different from using a search engine?
* What is the "autonomy" dial, and why does the risk change as autonomy increases?
* Describe Level 1 (autocomplete) AI assistance.
* Describe Level 2 (conversational) AI assistance.
* Describe Level 3 (in-editor chat with gated approval) and what defines this level.
* What two properties make a system "agentic"?
* What is the difference in blast radius between a gated (Level 3) and an autonomous (Level 4) tool?
* Why should you commit to git before running an agentic tool on a real project?
* Why are passing tests not a substitute for reading an agent's diff?
* What is GitHub Copilot?
* How do Copilot's autocomplete, chat, and agent modes map onto the levels of autonomy?
* What controls whether a Copilot agent operates at Level 3 versus Level 4?
* What should you watch for in Copilot's autocomplete suggestions, and why?
* What transfers between AI coding tools, and what merely changes?
* What does it mean to give context rather than just a request when prompting for code? Give a before/after example.
* Why would you ask a model to explain code before it modifies it?
* Why request tests alongside the implementation rather than afterwards?
* Why is AI particularly strong at writing tests, and what should you watch for?
* What makes good AI-generated documentation, and what is the failure mode to avoid?
* How is AI useful for code analysis, and what are its limits?
* What is AI most useful for in optimisation, and what does it fundamentally not know about your system?
* Why must you read AI-generated code before accepting it?
* What is the core security concern with pasting content into a public LLM?
* Is there a remedy once proprietary data has been submitted to a public model?
* What is the difference between a public tool like ChatGPT.com and an enterprise API with a data processing agreement?
* What is the implicit transmission problem with IDE-integrated tools?
* What is the hard rule about credentials, API keys, and customer data in prompts?
* What is a silent failure, and why is it more dangerous than a loud one?
* Why is a test suite written by the same model that wrote the code not a reliable safety net?
* Why must destructive or irreversible operations such as DROP, DELETE, or a schema migration always require human review?
* Why should you verify package names independently before installing them?
* Who owns the output of a deployed AI system?
* Where does bias in an AI model come from? 
* When selecting a third-party model, what should you review, and what does missing documentation signal?
* Why should AI outputs that inform high-stakes decisions have a human escalation path and be kept auditable?
* What is dependency confusion (package hallucination)?
* Walk through the attack chain that unfolds when a developer installs a hallucinated package.
* What is agentic overreach, and what controls limit it?
* What is skill atrophy, and why is it a risk for a development team?
* Why is AI described as a "force multiplier" for engineers who understand the domain?

## Stretch Questions

* What is the difference between narrow (weak) AI and general (strong) AI?
* Where does deep learning sit relative to machine learning, and what is a neural network loosely modelled on?
* What is reinforcement learning, and how does it differ from supervised and unsupervised learning?
* What is the difference between a feature and a label in a supervised learning dataset?
* What is the difference between a classification problem and a regression problem?
* What is overfitting, and why is it a problem?
* What is a "foundation model," and why is the term used?
* How does a text-generating LLM differ from a generative image model in terms of output and typical use?
* What is the transformer architecture, and what key mechanism does it rely on?
* What does it mean for a model to be "pre-trained," and how does pre-training relate to fine-tuning?
* What are embeddings, and where might they be used in a data product (for example, semantic search)?
* What is Retrieval-Augmented Generation (RAG), and what problem does it solve that a bare LLM cannot?
* What is "temperature," and how does it affect a model's output?
* How can you make an LLM's responses more deterministic, and when would you want to?
* Why might you set a maximum-token limit on a request, and what happens if a response is cut off mid-way?
* When would you deliberately choose a smaller, cheaper model over a larger, more capable one?
* How would you evaluate or benchmark whether a model is good enough for a specific task before shipping it?
* What is the difference between a system prompt and a user prompt?
* What is the difference between zero-shot, one-shot, and few-shot prompting?
* How would you prompt a model to return valid, machine-readable JSON, and why must you still validate the result?
* What does asking a model to "think step by step" (chain-of-thought) do, and why can it improve answers?
* Why can breaking a complex task into smaller sequential steps improve a model's output?
* What is a prompt injection attack, and how does it differ from SQL injection?
* Why should user input that gets inserted into a prompt be treated as untrusted?
* What is the risk of an LLM leaking its system prompt or other hidden context, and how might you mitigate it?