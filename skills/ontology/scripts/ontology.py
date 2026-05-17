#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ontology CLI - 知识图谱命令行工具

用法:
  python3 ontology.py create --type Person --props '{"name":"Alice"}'
  python3 ontology.py query --type Task --where '{"status":"open"}'
  python3 ontology.py relate --from proj_001 --rel has_task --to task_001
  python3 ontology.py validate
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 本体存储位置
GRAPH_FILE = Path(__file__).parent.parent.parent / "memory" / "ontology" / "graph.jsonl"
SCHEMA_FILE = Path(__file__).parent.parent.parent / "memory" / "ontology" / "schema.yaml"


def ensure_storage():
    """确保存储目录存在"""
    GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not GRAPH_FILE.exists():
        GRAPH_FILE.touch()


def generate_id(type_: str) -> str:
    """生成实体 ID"""
    prefix = type_.lower()[:3]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{timestamp}"


def create_entity(type_: str, props: dict):
    """创建实体"""
    entity = {
        "id": generate_id(type_),
        "type": type_,
        "properties": props,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat()
    }
    
    # 追加到图谱
    with open(GRAPH_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps({
            "op": "create",
            "entity": entity
        }, ensure_ascii=False) + '\n')
    
    print(f"✅ 创建实体：{entity['id']}")
    print(f"   类型：{type_}")
    print(f"   属性：{json.dumps(props, ensure_ascii=False)}")
    return entity


def query_entities(type_: str = None, where: dict = None):
    """查询实体"""
    ensure_storage()
    
    results = []
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry.get('op') == 'create':
                entity = entry['entity']
                
                # 类型过滤
                if type_ and entity.get('type') != type_:
                    continue
                
                # 属性过滤
                if where:
                    match = True
                    for key, value in where.items():
                        if entity.get('properties', {}).get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                results.append(entity)
    
    print(f"找到 {len(results)} 个实体:")
    for entity in results:
        print(f"\n  ID: {entity['id']}")
        print(f"  类型：{entity['type']}")
        print(f"  属性：{json.dumps(entity.get('properties', {}), ensure_ascii=False, indent=4)}")
    
    return results


def create_relation(from_id: str, rel: str, to_id: str):
    """创建关系"""
    relation = {
        "from_id": from_id,
        "relation_type": rel,
        "to_id": to_id,
        "created": datetime.now().isoformat()
    }
    
    # 追加到图谱
    with open(GRAPH_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps({
            "op": "relate",
            **relation
        }, ensure_ascii=False) + '\n')
    
    print(f"✅ 创建关系：{from_id} --[{rel}]--> {to_id}")
    return relation


def validate_graph():
    """验证图谱"""
    ensure_storage()
    
    errors = []
    entities = {}
    relations = []
    
    # 读取所有实体和关系
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry.get('op') == 'create':
                entity = entry['entity']
                entities[entity['id']] = entity
            elif entry.get('op') == 'relate':
                relations.append(entry)
    
    # 验证关系
    for rel in relations:
        from_id = rel.get('from_id')
        to_id = rel.get('to_id')
        
        if from_id not in entities:
            errors.append(f"❌ 关系 {rel['relation_type']} 的 from_id {from_id} 不存在")
        
        if to_id not in entities:
            errors.append(f"❌ 关系 {rel['relation_type']} 的 to_id {to_id} 不存在")
    
    # 报告结果
    if errors:
        print("验证失败:")
        for error in errors:
            print(error)
        return False
    else:
        print("✅ 图谱验证通过")
        print(f"   实体数：{len(entities)}")
        print(f"   关系数：{len(relations)}")
        return True


def list_entities(type_: str = None):
    """列出实体"""
    query_entities(type_=type_)


def get_entity(id_: str):
    """获取实体"""
    ensure_storage()
    
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry.get('op') == 'create':
                entity = entry['entity']
                if entity['id'] == id_:
                    print(f"实体：{id_}")
                    print(f"  类型：{entity['type']}")
                    print(f"  属性：{json.dumps(entity.get('properties', {}), ensure_ascii=False, indent=4)}")
                    print(f"  创建：{entity.get('created', 'N/A')}")
                    print(f"  更新：{entity.get('updated', 'N/A')}")
                    return entity
    
    print(f"❌ 未找到实体：{id_}")
    return None


def related_entities(id_: str, rel: str = None):
    """查询相关实体"""
    ensure_storage()
    
    results = []
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry.get('op') == 'relate':
                if entry.get('from_id') == id_:
                    if rel is None or entry.get('relation_type') == rel:
                        results.append(entry)
    
    print(f"找到 {len(results)} 个相关实体:")
    for r in results:
        print(f"  {r['from_id']} --[{r['relation_type']}]--> {r['to_id']}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Ontology CLI - 知识图谱工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # create 命令
    create_parser = subparsers.add_parser('create', help='创建实体')
    create_parser.add_argument('--type', required=True, help='实体类型')
    create_parser.add_argument('--props', required=True, help='属性 JSON')
    
    # query 命令
    query_parser = subparsers.add_parser('query', help='查询实体')
    query_parser.add_argument('--type', help='实体类型')
    query_parser.add_argument('--where', help='过滤条件 JSON')
    
    # relate 命令
    relate_parser = subparsers.add_parser('relate', help='创建关系')
    relate_parser.add_argument('--from', dest='from_id', required=True, help='源实体 ID')
    relate_parser.add_argument('--rel', required=True, help='关系类型')
    relate_parser.add_argument('--to', dest='to_id', required=True, help='目标实体 ID')
    
    # validate 命令
    subparsers.add_parser('validate', help='验证图谱')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出实体')
    list_parser.add_argument('--type', help='实体类型')
    
    # get 命令
    get_parser = subparsers.add_parser('get', help='获取实体')
    get_parser.add_argument('--id', required=True, help='实体 ID')
    
    # related 命令
    related_parser = subparsers.add_parser('related', help='查询相关实体')
    related_parser.add_argument('--id', required=True, help='实体 ID')
    related_parser.add_argument('--rel', help='关系类型')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        props = json.loads(args.props)
        create_entity(args.type, props)
    
    elif args.command == 'query':
        where = json.loads(args.where) if args.where else None
        query_entities(args.type, where)
    
    elif args.command == 'relate':
        create_relation(args.from_id, args.rel, args.to_id)
    
    elif args.command == 'validate':
        validate_graph()
    
    elif args.command == 'list':
        list_entities(args.type)
    
    elif args.command == 'get':
        get_entity(args.id)
    
    elif args.command == 'related':
        related_entities(args.id, args.rel)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
