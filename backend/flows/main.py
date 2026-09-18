"""CLI entry point for Stage 4: Automatic Flow Discovery + Editable Flow System.

Usage:
    python -m flows.main discover --understanding ./output/understanding/understanding.json --website-id ness
    python -m flows.main list --website-id ness
    python -m flows.main show --flow-id 1
    python -m flows.main rename --flow-id 1 --name "New Name"
    python -m flows.main add-step --flow-id 1 --type ask_followup --options "yes,no"
    python -m flows.main remove-step --flow-id 1 --index 2
    python -m flows.main reorder --flow-id 1 --order 2,0,1
    python -m flows.main publish --flow-id 1
    python -m flows.main unpublish --flow-id 1
"""
from __future__ import annotations

import argparse
import logging
import sys

from understanding.bedrock_client import BedrockClient

from .db import (
    add_step,
    delete_flow,
    get_connection,
    get_flow,
    init_schema,
    list_flows,
    remove_step,
    rename_flow,
    reorder_steps,
    set_published,
)
from .discovery import FlowDiscoveryEngine
from .models import FlowStep


def _print_flow(flow) -> None:
    status = "PUBLISHED" if flow.published else "draft"
    print(f"\n[{flow.id}] {flow.flow_name}  ({status})")
    print(f"  Triggers: {flow.trigger}")
    for i, step in enumerate(flow.steps):
        print(f"  Step {i}: {step.type} {step.options if step.options else ''}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flow discovery + editable flow CRUD (Stage 4).")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_p = subparsers.add_parser("discover", help="Auto-discover flows from Stage 2 understanding output")
    discover_p.add_argument("--understanding", default="./output/understanding/understanding.json")
    discover_p.add_argument("--website-id", default="ness")
    discover_p.add_argument("--model", default="amazon.nova-pro-v1:0")

    list_p = subparsers.add_parser("list", help="List all flows for a website")
    list_p.add_argument("--website-id", default="ness")

    show_p = subparsers.add_parser("show", help="Show one flow in detail")
    show_p.add_argument("--flow-id", type=int, required=True)

    rename_p = subparsers.add_parser("rename", help="Rename a flow")
    rename_p.add_argument("--flow-id", type=int, required=True)
    rename_p.add_argument("--name", required=True)

    add_step_p = subparsers.add_parser("add-step", help="Add a step to a flow")
    add_step_p.add_argument("--flow-id", type=int, required=True)
    add_step_p.add_argument("--type", required=True, choices=["show_options", "retrieve_information", "ask_followup", "collect_input", "call_action"])
    add_step_p.add_argument("--options", default="", help="Comma-separated option list")
    add_step_p.add_argument("--position", type=int, default=None)

    remove_step_p = subparsers.add_parser("remove-step", help="Remove a step by index")
    remove_step_p.add_argument("--flow-id", type=int, required=True)
    remove_step_p.add_argument("--index", type=int, required=True)

    reorder_p = subparsers.add_parser("reorder", help="Reorder steps")
    reorder_p.add_argument("--flow-id", type=int, required=True)
    reorder_p.add_argument("--order", required=True, help="Comma-separated new order of current indices, e.g. 2,0,1")

    publish_p = subparsers.add_parser("publish", help="Publish a flow")
    publish_p.add_argument("--flow-id", type=int, required=True)

    unpublish_p = subparsers.add_parser("unpublish", help="Unpublish a flow")
    unpublish_p.add_argument("--flow-id", type=int, required=True)

    delete_p = subparsers.add_parser("delete", help="Delete a flow")
    delete_p.add_argument("--flow-id", type=int, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    conn = get_connection()
    init_schema(conn)

    if args.command == "discover":
        client = BedrockClient(model_id=args.model, region_name=args.region)
        engine = FlowDiscoveryEngine(client)
        created = engine.run(conn, args.understanding, args.website_id)
        print(f"Discovered {len(created)} flows for website_id={args.website_id}")
        for flow in created:
            _print_flow(flow)

    elif args.command == "list":
        for flow in list_flows(conn, args.website_id):
            _print_flow(flow)

    elif args.command == "show":
        flow = get_flow(conn, args.flow_id)
        if flow is None:
            print(f"Flow {args.flow_id} not found")
        else:
            _print_flow(flow)

    elif args.command == "rename":
        rename_flow(conn, args.flow_id, args.name)
        _print_flow(get_flow(conn, args.flow_id))

    elif args.command == "add-step":
        options = [o.strip() for o in args.options.split(",") if o.strip()]
        step = FlowStep(type=args.type, options=options)
        flow = add_step(conn, args.flow_id, step, position=args.position)
        _print_flow(flow)

    elif args.command == "remove-step":
        flow = remove_step(conn, args.flow_id, args.index)
        _print_flow(flow)

    elif args.command == "reorder":
        order = [int(i.strip()) for i in args.order.split(",")]
        flow = reorder_steps(conn, args.flow_id, order)
        _print_flow(flow)

    elif args.command == "publish":
        flow = set_published(conn, args.flow_id, True)
        _print_flow(flow)

    elif args.command == "unpublish":
        flow = set_published(conn, args.flow_id, False)
        _print_flow(flow)

    elif args.command == "delete":
        delete_flow(conn, args.flow_id)
        print(f"Deleted flow {args.flow_id}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
