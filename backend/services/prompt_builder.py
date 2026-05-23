class PromptBuilder:


    @staticmethod
    def build(schema, question):


        prompt = """
You are an expert SQL assistant.

Generate ONLY valid SQL.

Rules:

1. Return only SQL
2. Never use DROP
3. Never use DELETE
4. Use only available tables
5. Use only available columns


Database Schema:

"""


        for table,data in schema.items():

            prompt += f"\nTABLE {table}\n"


            for col in data["columns"]:

                prompt += (

                    f"- "

                    f"{col['name']} "

                    f"({col['type']})\n"

                )


        prompt += f"""

Question:

{question}


SQL:

"""


        return prompt