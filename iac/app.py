from aws_cdk import App

from iac.stack import RAGStack



app = App()


RAGStack(app, "RAGStack")

app.synth()
