"""MCP Server implementation using FastMCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from codelens.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP("CodeLens")


@mcp.tool()
def search_nodes(keyword: str) -> str:
    """Native Lucene full-text search on node names, docstrings, and file paths.
    
    Use this to find entry points in the codebase when native file search is insufficient.
    
    Args:
        keyword: The search term (can include wildcards like *).
    """
    client = Neo4jClient()
    try:
        with client.session() as session:
            # First, ensure the index exists (this is safe to call multiple times)
            session.run("""
                CREATE FULLTEXT INDEX node_search IF NOT EXISTS 
                FOR (n:Class|Function|Interface|Constructor) 
                ON EACH [n.name, n.docstring, n.signature, n.filepath]
            """)
            
            # Now query the index
            query = """
            CALL db.index.fulltext.queryNodes("node_search", $keyword) YIELD node, score
            RETURN labels(node)[0] AS type, node.name AS name, node.filepath AS filepath, node.signature AS signature, node.docstring AS docstring, score
            ORDER BY score DESC LIMIT 10
            """
            result = session.run(query, keyword=keyword)
            
            output = []
            for record in result:
                item = f"[{record['type']}] {record['name']} (File: {record['filepath']})\n"
                if record['signature']:
                    item += f"  Signature: {record['signature']}\n"
                if record['docstring']:
                    # Truncate docstring to keep it concise
                    doc = record['docstring'][:100] + ("..." if len(record['docstring']) > 100 else "")
                    item += f"  Doc: {doc}\n"
                output.append(item)
                
            if not output:
                return f"No nodes found matching keyword: {keyword}"
            return "\n".join(output)
    except Exception as e:
        logger.error(f"Error in search_nodes: {e}")
        return f"Error executing search: {e}"
    finally:
        client.close()


@mcp.tool()
def get_code_context(symbol_name: str) -> str:
    """Returns the multi-hop structural context around a function or class.
    
    This includes the node itself, its direct callers, direct callees, and 
    any conditional branches inside it.
    
    Args:
        symbol_name: The exact name of the function or class.
    """
    client = Neo4jClient()
    try:
        with client.session() as session:
            # Find the center node
            query = """
            MATCH (center)
            WHERE center.name = $symbol_name AND center:Unresolved = false
            
            // Get callers
            OPTIONAL MATCH (caller)-[:calls]->(center)
            
            // Get callees
            OPTIONAL MATCH (center)-[:calls]->(callee)
            
            // Get branches
            OPTIONAL MATCH (center)-[:has_branch]->(branch)
            
            RETURN 
                labels(center)[0] AS type, center.filepath AS filepath, center.signature AS signature,
                collect(DISTINCT caller.name) AS callers,
                collect(DISTINCT callee.name) AS callees,
                collect(DISTINCT branch.name) AS branches
            LIMIT 1
            """
            result = session.run(query, symbol_name=symbol_name).single()
            
            if not result:
                return f"Symbol '{symbol_name}' not found in the graph."
                
            output = [
                f"Context for [{result['type']}] {symbol_name}",
                f"File: {result['filepath']}",
                f"Signature: {result['signature'] or 'N/A'}",
                "-" * 40,
                "Callers (Who calls this?):",
            ]
            
            callers = [c for c in result["callers"] if c]
            if callers:
                for c in callers:
                    output.append(f"  - {c}")
            else:
                output.append("  (None or unresolved)")
                
            output.append("\nCallees (What does this call?):")
            callees = [c for c in result["callees"] if c]
            if callees:
                for c in callees:
                    output.append(f"  - {c}")
            else:
                output.append("  (None or external)")
                
            output.append("\nConditional Branches (Internal logic flow):")
            branches = [b for b in result["branches"] if b]
            if branches:
                for b in branches:
                    output.append(f"  - {b}")
            else:
                output.append("  (None)")
                
            return "\n".join(output)
    except Exception as e:
        logger.error(f"Error in get_code_context: {e}")
        return f"Error executing context fetch: {e}"
    finally:
        client.close()


@mcp.tool()
def get_callers(symbol_name: str) -> str:
    """Returns all functions or classes that call/depend on the given symbol.
    
    Use this for impact analysis (e.g., "If I change X, what breaks?").
    
    Args:
        symbol_name: The exact name of the function or class.
    """
    client = Neo4jClient()
    try:
        with client.session() as session:
            query = """
            MATCH (caller)-[:calls]->(target)
            WHERE target.name = $symbol_name
            RETURN labels(caller)[0] AS type, caller.name AS name, caller.filepath AS filepath
            """
            result = session.run(query, symbol_name=symbol_name)
            
            output = [f"Callers of '{symbol_name}':"]
            found = False
            for record in result:
                found = True
                output.append(f"  - [{record['type']}] {record['name']} (in {record['filepath']})")
                
            if not found:
                return f"No callers found for '{symbol_name}'."
            return "\n".join(output)
    except Exception as e:
        return f"Error executing get_callers: {e}"
    finally:
        client.close()


@mcp.tool()
def get_callees(symbol_name: str) -> str:
    """Returns all functions or classes that the given symbol calls/depends on.
    
    Args:
        symbol_name: The exact name of the function or class.
    """
    client = Neo4jClient()
    try:
        with client.session() as session:
            query = """
            MATCH (source)-[:calls]->(callee)
            WHERE source.name = $symbol_name AND source:Unresolved = false
            RETURN labels(callee)[0] AS type, callee.name AS name
            """
            result = session.run(query, symbol_name=symbol_name)
            
            output = [f"Symbols called by '{symbol_name}':"]
            found = False
            for record in result:
                found = True
                output.append(f"  - [{record['type']}] {record['name']}")
                
            if not found:
                return f"'{symbol_name}' does not call any internal symbols."
            return "\n".join(output)
    except Exception as e:
        return f"Error executing get_callees: {e}"
    finally:
        client.close()


@mcp.tool()
def get_domains() -> str:
    """Returns a list of all discovered business domains in the codebase.
    
    Use this to get a high-level overview of the system architecture.
    """
    client = Neo4jClient()
    try:
        with client.session() as session:
            query = """
            MATCH (d:Domain)
            OPTIONAL MATCH (n)-[:IN_DOMAIN]->(d)
            RETURN d.name AS name, d.summary AS summary, count(n) AS member_count
            ORDER BY member_count DESC
            """
            result = session.run(query)
            
            output = ["Discovered Business Domains:"]
            found = False
            for record in result:
                found = True
                output.append(f"\n- {record['name']} ({record['member_count']} internal nodes)")
                output.append(f"  Summary: {record['summary']}")
                
            if not found:
                return "No domains found. Run clustering first."
            return "\n".join(output)
    except Exception as e:
        return f"Error executing get_domains: {e}"
    finally:
        client.close()


@mcp.tool()
def get_domain(domain_name: str) -> str:
    """Returns the full context and all member nodes of a specific business domain.
    
    Args:
        domain_name: The exact name of the domain (e.g., 'Domain 2').
    """
    client = Neo4jClient()
    try:
        with client.session() as session:
            query = """
            MATCH (d:Domain {name: $domain_name})
            OPTIONAL MATCH (n)-[:IN_DOMAIN]->(d)
            RETURN d.summary AS summary, collect(n) AS members
            """
            record = session.run(query, domain_name=domain_name).single()
            
            if not record:
                return f"Domain '{domain_name}' not found."
                
            output = [
                f"=== {domain_name} ===",
                f"Summary: {record['summary']}",
                "\nMembers:"
            ]
            
            for m in record['members']:
                if m:
                    label = list(m.labels)[0] if m.labels else "Unknown"
                    output.append(f"  - [{label}] {m.get('name', 'unnamed')}")
                    
            return "\n".join(output)
    except Exception as e:
        return f"Error executing get_domain: {e}"
    finally:
        client.close()
