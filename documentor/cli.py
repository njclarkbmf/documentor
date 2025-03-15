"""
Command-line interface for the Documetor package.
"""

import json
import os
from typing import Optional, Dict, Any, List

import typer
from rich.json import JSON
from rich.console import Console
from rich.table import Table

from documetor.config import (
    logger, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, DEFAULT_LOCATION,
    DEFAULT_EMBEDDING_MODEL, DEFAULT_BATCH_SIZE, DEFAULT_MAX_WORKERS,
    DEFAULT_CHUNK_STRATEGY, get_default_project_id
)
from documetor.core.embedder import DocumentEmbedder

# Initialize CLI app
app = typer.Typer(
    help="Document embeddings and semantic search tool",
    add_completion=False
)


@app.callback()
def callback():
    """
    Documetor - Document embeddings and semantic search with Google Vertex AI.
    """
    pass
console = Console()


@app.command("search")
def search_command(
    project_id: str = typer.Option(None, "--project-id", help="Google Cloud project ID"),
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to return"),
    store_type: str = typer.Option("local", "--store-type", help="Vector store type (local or vertex)"),
    store_path: Optional[str] = typer.Option(None, "--store-path", help="Path to local vector store"),
    index_name: Optional[str] = typer.Option(None, "--index-name", help="Name for Vertex Matching Engine index"),
    location: str = typer.Option(DEFAULT_LOCATION, "--location", help="Google Cloud region"),
    embedding_model: str = typer.Option(DEFAULT_EMBEDDING_MODEL, "--embedding-model", help="Vertex AI model for embeddings"),
    filter_source: Optional[str] = typer.Option(None, "--filter-source", help="Filter results by source"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    silent: bool = typer.Option(False, "--silent", "-s", help="Suppress all output"),
    output_format: str = typer.Option("text", "--output-format", "-o", help="Output format (text, json)"),
):
    """Search for documents using vector similarity"""
    try:
        # Get project ID if not provided
        if project_id is None:
            project_id = get_default_project_id()
            if project_id is None:
                console.print("[red]Error: Project ID not provided and could not be detected automatically.[/red]")
                console.print("Please specify a project ID with --project-id or set the GOOGLE_CLOUD_PROJECT environment variable.")
                raise typer.Exit(code=1)
        
        # Create embedder
        embedder = DocumentEmbedder(
            project_id=project_id,
            location=location,
            embedding_model=embedding_model,
            store_type=store_type,
            store_path=store_path,
            index_name=index_name,
            verbose=verbose,
            silent=silent
        )
        
        # Prepare filters
        filters = {}
        if filter_source:
            filters["source"] = filter_source
        
        # Perform search
        results = embedder.search(query, top_k=top_k, filters=filters)
        
        # Display results
        if not silent:
            if output_format == "json":
                console.print(JSON(json.dumps(results)))
            else:
                _display_search_results(results, query)
        
        return results
        
    except Exception as e:
        if not silent:
            console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Error in search command: {str(e)}")
        raise typer.Exit(code=1)


def _display_search_results(results: List[Dict[str, Any]], query: str):
    """Display search results in a nicely formatted table"""
    console.print(f"Search query: [bold cyan]{query}[/bold cyan]")
    console.print(f"Found {len(results)} results\n")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Score", style="cyan", width=8)
    table.add_column("Source", style="green")
    table.add_column("Content", width=80)
    
    for result in results:
        # Format the source path to be more readable
        source = os.path.basename(result["source"])
        
        # Format the similarity score
        score = f"{result['similarity']:.4f}"
        
        # Truncate the text if it's too long
        text = result.get("text", "")
        if len(text) > 200:
            text = text[:197] + "..."
        
        table.add_row(score, source, text)
    
    console.print(table)


@app.command("info")
def info_command(
    store_path: str = typer.Option(..., "--store-path", help="Path to local vector store"),
):
    """Display information about a local vector store"""
    try:
        if not os.path.exists(store_path):
            console.print(f"[red]Error: Vector store file not found: {store_path}[/red]")
            raise typer.Exit(code=1)
        
        # Load the vector store
        import pickle
        with open(store_path, 'rb') as f:
            embeddings, metadata = pickle.load(f)
        
        # Collect stats
        num_documents = len({meta["source"] for meta in metadata})
        sources = sorted({meta["source"] for meta in metadata})
        chunks_per_source = {}
        for meta in metadata:
            source = meta["source"]
            chunks_per_source[source] = chunks_per_source.get(source, 0) + 1
        
        # Display info
        console.print(f"[bold]Vector Store: {store_path}[/bold]")
        console.print(f"Total vectors: {len(embeddings)}")
        console.print(f"Total documents: {num_documents}")
        console.print(f"Vector dimensions: {len(embeddings[0]) if embeddings else 'N/A'}")
        
        console.print("\n[bold]Documents:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Document", style="green")
        table.add_column("Chunks", style="cyan", justify="right")
        
        for source in sources:
            table.add_row(source, str(chunks_per_source[source]))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Error in info command: {str(e)}")
        raise typer.Exit(code=1)


@app.command("process")
def process(
    project_id: str = typer.Option(None, "--project-id", help="Google Cloud project ID"),
    directory: str = typer.Option(..., "--directory", "-d", help="Directory containing documents"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Process subdirectories recursively"),
    store_type: str = typer.Option("local", "--store-type", help="Vector store type (local or vertex)"),
    store_path: Optional[str] = typer.Option(None, "--store-path", help="Path to save/load local vector store"),
    index_name: Optional[str] = typer.Option(None, "--index-name", help="Name for Vertex Matching Engine index"),
    location: str = typer.Option(DEFAULT_LOCATION, "--location", help="Google Cloud region"),
    chunk_size: int = typer.Option(DEFAULT_CHUNK_SIZE, "--chunk-size", help="Maximum size of text chunks"),
    chunk_overlap: int = typer.Option(DEFAULT_CHUNK_OVERLAP, "--chunk-overlap", help="Overlap between consecutive chunks"),
    chunk_strategy: str = typer.Option(DEFAULT_CHUNK_STRATEGY, "--chunk-strategy", help="Strategy for chunking (hybrid, sentence, fixed)"),
    embedding_model: str = typer.Option(DEFAULT_EMBEDDING_MODEL, "--embedding-model", help="Vertex AI model for embeddings"),
    batch_size: int = typer.Option(DEFAULT_BATCH_SIZE, "--batch-size", help="Number of documents to process in batch"),
    max_workers: int = typer.Option(DEFAULT_MAX_WORKERS, "--max-workers", help="Maximum number of concurrent workers"),
    use_ocr: bool = typer.Option(False, "--use-ocr", help="Use OCR for PDF text extraction"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    silent: bool = typer.Option(False, "--silent", "-s", help="Suppress all output"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
):
    """Process documents in a directory and create embeddings"""
    try:
        # Get project ID if not provided
        if project_id is None:
            project_id = get_default_project_id()
            if project_id is None:
                console.print("[red]Error: Project ID not provided and could not be detected automatically.[/red]")
                console.print("Please specify a project ID with --project-id or set the GOOGLE_CLOUD_PROJECT environment variable.")
                raise typer.Exit(code=1)
        
        # Create embedder
        embedder = DocumentEmbedder(
            project_id=project_id,
            location=location,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_strategy=chunk_strategy,
            embedding_model=embedding_model,
            store_type=store_type,
            store_path=store_path,
            index_name=index_name,
            batch_size=batch_size,
            max_workers=max_workers,
            use_ocr=use_ocr,
            verbose=verbose,
            silent=silent,
            log_level=log_level
        )
        
        # Process directory
        embedder.process_directory(directory, recursive=recursive)
        
        if not silent:
            console.print("[green]Processing completed successfully![/green]")
    
    except Exception as e:
        if not silent:
            console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Error in process command: {str(e)}")
        raise typer.Exit(code=1)
