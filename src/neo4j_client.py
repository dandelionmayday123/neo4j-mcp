import os
import logging
from .config import config
import httpx
from typing import Any, Dict, List, Optional
import json
import base64
import codecs

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        # 配置代理
        self.proxies = {}
        if config.HTTP_PROXY:
            self.proxies["http://"] = config.HTTP_PROXY
        if config.HTTPS_PROXY:
            self.proxies["https://"] = config.HTTPS_PROXY
        
        # 基本认证
        auth_string = f"{config.NEO4J_USERNAME}:{config.NEO4J_PASSWORD}"
        self.auth_header = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        
        # API端点
        self.transaction_endpoint = f"{config.NEO4J_URI}/db/data/transaction/commit"
        
        # 创建异步客户端
        transport = None
        if config.HTTP_PROXY:
            transport = httpx.AsyncHTTPTransport(proxy=config.HTTP_PROXY)
            
        self.client = httpx.AsyncClient(
            transport=transport,
            headers={
                "Authorization": f"Basic {self.auth_header}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json"
            },
            verify=False  # 如果需要跳过SSL验证
        )
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
        
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        data = {
            "statements": [{
                "statement": query,
                "parameters": params or {}
            }]
        }
        
        try:
            # 记录请求数据
            logging.debug(f"发送请求到 {self.transaction_endpoint}")
            json_data = json.dumps(data, ensure_ascii=False)
            logging.debug(f"请求数据: {json_data}")
            
            response = await self.client.post(
                self.transaction_endpoint,
                content=json_data.encode('utf-8')
            )
            response.raise_for_status()
            
            # 记录原始响应
            raw_response = response.text
            logging.debug(f"收到原始响应: {raw_response}")
            
            try:
                # 使用utf-8解码响应内容
                result = json.loads(raw_response)
            except json.JSONDecodeError as e:
                logging.error(f"JSON解析错误: {str(e)}")
                logging.error(f"原始响应内容: {raw_response}")
                raise Exception(f"JSON解析失败: {str(e)}")
            
            # 检查错误
            if result.get("errors"):
                error_msg = result["errors"][0]["message"]
                logging.error(f"Neo4j返回错误: {error_msg}")
                raise Exception(error_msg)
                
            # 处理结果
            if not result["results"]:
                return []
                
            # 转换结果格式
            columns = result["results"][0]["columns"]
            rows = []
            for row in result["results"][0]["data"]:
                row_dict = {}
                for col, val in zip(columns, row["row"]):
                    row_dict[col] = val
                rows.append(row_dict)
                
            return rows
            
        except httpx.HTTPError as e:
            logging.error(f"HTTP请求错误: {str(e)}")
            raise Exception(f"HTTP请求错误: {str(e)}")
        except Exception as e:
            logging.error(f"未预期的错误: {str(e)}")
            raise
            
    async def create_node(self, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """创建节点"""
        query = f"""
        CREATE (n:{label} $props)
        RETURN n
        """
        result = await self.execute_query(query, {"props": properties})
        return result[0] if result else None
        
    async def create_relationship(
        self,
        from_node_id: int,
        to_node_id: int,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建关系"""
        try:
            logging.info(f"创建关系 {rel_type} 从节点 {from_node_id} 到节点 {to_node_id}")
            # 如果properties为None，使用空字典
            props = properties if properties is not None else {}
            query = f"""
            MATCH (from) WHERE ID(from) = $from_id
            MATCH (to) WHERE ID(to) = $to_id
            CREATE (from)-[r:{rel_type}]->(to)
            SET r = $props
            RETURN r
            """
            params = {
                "from_id": from_node_id,
                "to_id": to_node_id,
                "props": props
            }
            result = await self.execute_query(query, params)
            logging.info("关系创建成功")
            return result[0] if result else None
        except Exception as e:
            logging.error(f"关系创建失败: {str(e)}")
            raise