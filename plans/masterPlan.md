EchoPilot - Customer success copilot

# Goal and vision:
EchoPilot acts as the go-to solution for support by both internal associates and customers by automating the major tasks of a customer support team. It will be used for answering queries, registering customer complaint ticket, feature request ticket from associates. There will be 2 modes - Associate and Customer. It uses RAG with intent analysis and tool calling.

# Data collections:
1. internal knowledge base (financial data, team and structure, patents)
2. general knowledge base (services, FAQs, troubleshooting steps, TnCs)
3. associate chat
4. customer chat

# App workflow(customer side):
1. user add input text with an image
2. EchoPilot does intent analysis between query, complaint or service request.
3. if its a complaint, it checks for the validity of the user claim from the general knowledge base
4. if complaint is invalid then a proper reasoning is given
5. else if the complaint is valid then a jira complaint ticket is raised for the support team to look into. Jira ticket id is given to customer for reference.
6. if it was a query then the best answer is provided.

# importnat considerations
1. Tool calling should be made for jira ticket making for complaint and service request ticket creation
2. summary should be created from closed chat sessions that could be used later for faster search. Ensure it has proper user request, solution provided and conclusion.
3. current context of the chat is important for user experience
4. associate has access to all chat history summaries and knowledge base.
5. customer has access to only general knowledge base and customer chat history
6. After jira ticket is created its give
7. ticket creation -  complaint ticket (customer), feature request ticket (associate), service request (customer). They are all the same just have proper naming and tag of associate or customer.

# tech-stack:
1. Google gemini 2.5 flash
2. jira for ticket creation
3. low code frontend - streamlit
4. python
5. langchain
6. chromaDB - cloud based vector database
7. locally run embedding model - (sentence-transformers/all-MiniLM-L6-v2)