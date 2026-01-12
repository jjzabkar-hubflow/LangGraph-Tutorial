import os

from src.agents.graph_builder import my_graph

current_directory = os.path.dirname(os.path.abspath(__file__))


def create_mermaid_diagram_files():
    # Render main graph with xray=True to expand all subgraphs
    mermaid_md = my_graph.get_graph(xray=True).draw_mermaid()
    mermaid_md_file = os.path.join(current_directory, "README.md")
    with open(mermaid_md_file, "w") as file:
        file.write('# Mermaid diagram with expanded subgraphs\n\n')
        file.write('This diagram shows the complete graph hierarchy including all subgraphs expanded using `xray=True`.\n\n')
        file.write('![Complete Graph](mermaid.png)\n')
        file.write(f'```mermaid\n{mermaid_md}\n```\n')

    # Generate PNG for complete graph with expanded subgraphs
    mermaid_png_file = os.path.join(current_directory, "mermaid.png")
    my_graph.get_graph(xray=True).draw_mermaid_png(output_file_path=mermaid_png_file)