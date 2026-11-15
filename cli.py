#!/usr/bin/env python3
"""
Bulk Domain Scanner CLI
High-performance asynchronous domain availability scanner.
Reads domain lists from files, command line, or stdin, and outputs available domains to buy.
"""

import argparse
import asyncio
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from core.checker import CheckResult, DomainChecker, DomainStatus, clean_domain

console = Console()

def load_domains_from_file(file_path: str) -> List[str]:
    """Load domains from a text, CSV, or raw list file."""
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: [yellow]{file_path}[/yellow]")
        sys.exit(1)

    raw_items: List[str] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        # Check if CSV
        if path.suffix.lower() == ".csv":
            first_line = f.readline()
            delimiter = ";" if ";" in first_line else ","
            f.seek(0)
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                for cell in row:
                    cell = cell.strip()
                    if cell and not cell.startswith("#"):
                        raw_items.append(cell)
        else:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.replace(",", " ").split() if p.strip()]
                raw_items.extend(parts)

    cleaned = []
    seen = set()
    for item in raw_items:
        cd = clean_domain(item)
        if cd and cd not in seen:
            seen.add(cd)
            cleaned.append(cd)

    return cleaned

def export_results(
    results: List[CheckResult],
    output_path: Optional[str] = None,
    available_txt_path: Optional[str] = None,
):
    """Save scan results to CSV, JSON, or plain text."""
    if available_txt_path:
        out_p = Path(available_txt_path).expanduser().resolve()
        avail_domains = [r.domain for r in results if r.status == DomainStatus.AVAILABLE]
        with open(out_p, "w", encoding="utf-8") as f:
            for d in avail_domains:
                f.write(f"{d}\n")
        console.print(f"[bold green]✔[/bold green] Exported [bold]{len(avail_domains)}[/bold] available domains to [cyan]{out_p}[/cyan]")

    if output_path:
        out_p = Path(output_path).expanduser().resolve()
        is_json = out_p.suffix.lower() == ".json"

        if is_json:
            data = [
                {
                    "domain": r.domain,
                    "status": r.status.value,
                    "stage": r.stage,
                    "reason": r.reason,
                    "duration_seconds": round(r.duration, 3),
                    "buy_links": r.buy_links,
                }
                for r in results
            ]
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            console.print(f"[bold green]✔[/bold green] Exported [bold]{len(results)}[/bold] results to JSON: [cyan]{out_p}[/cyan]")
        else:
            with open(out_p, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["domain", "status", "stage", "reason", "duration_sec", "porkbun_link", "namecheap_link", "godaddy_link"])
                for r in results:
                    writer.writerow([
                        r.domain,
                        r.status.value,
                        r.stage,
                        r.reason,
                        f"{r.duration:.2f}",
                        r.buy_links.get("Porkbun", ""),
                        r.buy_links.get("Namecheap", ""),
                        r.buy_links.get("GoDaddy", ""),
                    ])
            console.print(f"[bold green]✔[/bold green] Exported [bold]{len(results)}[/bold] results to CSV: [cyan]{out_p}[/cyan]")

def display_results_table(results: List[CheckResult], only_available: bool = False):
    """Display scan results in a rich styled table."""
    table = Table(title="Bulk Domain Availability Scan Results", header_style="bold magenta", expand=True)

    table.add_column("Domain", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center", no_wrap=True)
    table.add_column("Stage", justify="center", style="dim", no_wrap=True)
    table.add_column("Verification Detail", style="white")
    table.add_column("Buy Domain", style="blue")

    for r in results:
        if only_available and r.status != DomainStatus.AVAILABLE:
            continue

        if r.status == DomainStatus.AVAILABLE:
            status_text = Text("AVAILABLE", style="bold green on black")
            buy_text = f"[link={r.buy_links.get('Porkbun', '#')}]Porkbun[/link] | [link={r.buy_links.get('Namecheap', '#')}]Namecheap[/link] | [link={r.buy_links.get('GoDaddy', '#')}]GoDaddy[/link]"
        elif r.status == DomainStatus.TAKEN:
            status_text = Text("TAKEN", style="bold red")
            buy_text = "[dim]Unavailable[/dim]"
        elif r.status == DomainStatus.INVALID:
            status_text = Text("INVALID", style="yellow")
            buy_text = "[dim]-[/dim]"
        else:
            status_text = Text("UNKNOWN", style="bold yellow")
            buy_text = f"[link={r.buy_links.get('Namecheap', '#')}]Check Manually[/link]"

        table.add_row(
            r.domain,
            status_text,
            r.stage,
            r.reason,
            buy_text,
        )

    console.print(table)

def print_summary(results: List[CheckResult], elapsed_time: float):
    """Print scan performance summary."""
    total = len(results)
    available = sum(1 for r in results if r.status == DomainStatus.AVAILABLE)
    taken = sum(1 for r in results if r.status == DomainStatus.TAKEN)
    unknown = sum(1 for r in results if r.status == DomainStatus.UNKNOWN)
    invalid = sum(1 for r in results if r.status == DomainStatus.INVALID)

    summary_text = (
        f"[bold]Total Checked:[/bold] {total} domains in [cyan]{elapsed_time:.2f}s[/cyan] "
        f"([cyan]{(total / max(0.001, elapsed_time)):.1f}[/cyan] domains/sec)\n"
        f"🟢 [bold green]Available to Buy:[/bold green] [bold]{available}[/bold]   "
        f"🔴 [bold red]Taken:[/bold red] {taken}   "
        f"🟡 [bold yellow]Unknown:[/bold yellow] {unknown}   "
        f"⚪ [dim]Invalid:[/dim] {invalid}"
    )

    console.print(Panel(summary_text, title="Scan Summary", border_style="green" if available > 0 else "blue"))

async def async_main():
    parser = argparse.ArgumentParser(
        description="Bulk Domain Scanner: High-speed async domain availability checker with 1-click buy links.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan domains from a text or CSV file
  ./domain-scanner -f domains.txt

  # Scan domains and show ONLY available ones
  ./domain-scanner -f domains.txt --only-available

  # Scan domains and export available ones to available.txt
  ./domain-scanner -f domains.txt -a available.txt -o results.csv --only-available

  # Scan specific domains directly
  ./domain-scanner -d mybrandname2026.com superfastai.io google.com

  # Pipe domains from another command
  cat domains.txt | ./domain-scanner
        """,
    )

    parser.add_argument("-f", "--file", help="Path to file containing domain names (.txt, .csv)")
    parser.add_argument("-d", "--domains", nargs="+", help="One or more domain names to scan")
    parser.add_argument("positional_domains", nargs="*", help="Domain names passed without -d flag")

    parser.add_argument("--only-available", action="store_true", help="Only display available domains in output table")
    parser.add_argument("-a", "--output-available", help="Export available domains to a plain text file (one per line)")
    parser.add_argument("-o", "--output", help="Export full results to CSV or JSON file")

    parser.add_argument("-c", "--concurrency", type=int, default=30, help="Max DNS concurrency (default: 30)")
    parser.add_argument("--timeout", type=float, default=4.0, help="Timeout per query in seconds (default: 4.0)")

    args = parser.parse_args()

    # Determine input domains
    domain_list: List[str] = []

    if args.file:
        domain_list = load_domains_from_file(args.file)
    elif args.domains:
        domain_list = [clean_domain(d) or d.strip().lower() for d in args.domains if d.strip()]
    elif args.positional_domains:
        domain_list = [clean_domain(d) or d.strip().lower() for d in args.positional_domains if d.strip()]
    elif not sys.stdin.isatty():
        # Input piped via stdin
        raw_lines = sys.stdin.read().splitlines()
        for line in raw_lines:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = [p.strip() for p in line.replace(",", " ").split() if p.strip()]
                for p in parts:
                    cd = clean_domain(p)
                    if cd:
                        domain_list.append(cd)
    else:
        # Interactive prompt if executed with no arguments
        console.print(Panel.fit(
            "[bold cyan]Bulk Domain Scanner[/bold cyan]\n"
            "High-speed DNS + RDAP + WHOIS scanner with 1-click buy links",
            border_style="cyan"
        ))
        console.print("[1] Scan a file (.txt or .csv)")
        console.print("[2] Enter domain names manually")
        console.print("[3] Exit")

        choice = console.input("\n[bold yellow]Select an option [1-3]: [/bold yellow]").strip()
        if choice == "1":
            filepath = console.input("[bold]Enter file path: [/bold]").strip()
            domain_list = load_domains_from_file(filepath)
        elif choice == "2":
            raw_input = console.input("[bold]Enter domains (separated by space or comma): [/bold]").strip()
            parts = [d.strip() for d in raw_input.replace(",", " ").split() if d.strip()]
            domain_list = [clean_domain(d) or d.lower() for d in parts]
        else:
            return

    # Deduplicate while preserving order
    deduped_domains: List[str] = []
    seen = set()
    for d in domain_list:
        if d and d not in seen:
            seen.add(d)
            deduped_domains.append(d)

    if not deduped_domains:
        console.print("[bold red]No valid domains found to scan![/bold red]")
        sys.exit(1)

    console.print(f"\n[bold green]Starting bulk scan of {len(deduped_domains)} domains...[/bold green]\n")

    checker = DomainChecker(
        dns_concurrency=args.concurrency,
        timeout=args.timeout,
    )

    start_total_t = time.perf_counter()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning domains...", total=len(deduped_domains))

        def on_prog(res: CheckResult, current: int, total: int):
            status_style = "green" if res.status == DomainStatus.AVAILABLE else "red" if res.status == DomainStatus.TAKEN else "yellow"
            progress.update(task, advance=1, description=f"[cyan]Checked: [white]{res.domain}[/white] ([{status_style}]{res.status.value}[/{status_style}])")

        results = await checker.check_all(deduped_domains, on_progress=on_prog)

    elapsed = time.perf_counter() - start_total_t

    # Sort results: AVAILABLE first, then UNKNOWN, then TAKEN
    status_order = {DomainStatus.AVAILABLE: 0, DomainStatus.UNKNOWN: 1, DomainStatus.TAKEN: 2, DomainStatus.INVALID: 3}
    sorted_results = sorted(results, key=lambda x: (status_order[x.status], x.domain))

    # Display results table
    console.print()
    display_results_table(sorted_results, only_available=args.only_available)

    # Print summary statistics
    console.print()
    print_summary(sorted_results, elapsed)

    # Export if requested
    if args.output or args.output_available:
        export_results(sorted_results, args.output, args.output_available)

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan interrupted by user.[/yellow]")
        sys.exit(0)

if __name__ == "__main__":
    main()
