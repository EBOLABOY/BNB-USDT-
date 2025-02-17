from aiohttp import web
import os
from helpers import LogConfig
import aiofiles
import logging
from datetime import datetime
import psutil

class IPLogger:
    def __init__(self):
        self.ip_records = []  # 存储IP访问记录
        self.max_records = 100  # 最多保存100条记录

    def add_record(self, ip, path):
        # 查找是否存在相同IP的记录
        for record in self.ip_records:
            if record['ip'] == ip:
                # 如果找到相同IP，只更新时间
                record['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                record['path'] = path  # 更新访问路径
                return
        
        # 如果是新IP，添加新记录
        record = {
            'ip': ip,
            'path': path,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.ip_records.append(record)
        
        # 如果超出最大记录数，删除最早的记录
        if len(self.ip_records) > self.max_records:
            self.ip_records.pop(0)

    def get_records(self):
        return self.ip_records

def get_system_stats():
    """获取系统资源使用情况"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_used = memory.used / (1024 * 1024 * 1024)  # 转换为GB
    memory_total = memory.total / (1024 * 1024 * 1024)
    return {
        'cpu_percent': cpu_percent,
        'memory_used': round(memory_used, 2),
        'memory_total': round(memory_total, 2),
        'memory_percent': memory.percent
    }

async def handle_log(request):
    try:
        # 记录IP访问
        ip = request.remote
        request.app['ip_logger'].add_record(ip, request.path)
        
        # 获取系统资源状态
        system_stats = get_system_stats()
        
        log_path = os.path.join(LogConfig.LOG_DIR, 'trading_system.log')
        if not os.path.exists(log_path):
            return web.Response(text="日志文件不存在", status=404)
            
        async with aiofiles.open(log_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            
        lines = content.strip().split('\n')
        lines.reverse()
        content = '\n'.join(lines)
            
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>网格交易监控系统</title>
            <meta charset="utf-8">
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                .grid-container {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 1rem;
                    padding: 1rem;
                }}
                .card {{
                    background: white;
                    border-radius: 0.5rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    padding: 1rem;
                }}
                .status-value {{
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .profit {{ color: #10b981; }}
                .loss {{ color: #ef4444; }}
                .log-container {{
                    height: calc(100vh - 400px);
                    overflow-y: auto;
                    background: #1e1e1e;
                    color: #d4d4d4;
                    padding: 1rem;
                    border-radius: 0.5rem;
                }}
            </style>
        </head>
        <body class="bg-gray-100">
            <div class="container mx-auto px-4 py-8">
                <h1 class="text-3xl font-bold mb-8 text-center text-gray-800">网格交易监控系统</h1>
                
                <!-- 状态卡片 -->
                <div class="grid-container mb-8">
                    <div class="card">
                        <h2 class="text-lg font-semibold mb-4">基本信息</h2>
                        <div class="space-y-2">
                            <div class="flex justify-between">
                                <span>交易对</span>
                                <span class="status-value">BNB/USDT</span>
                            </div>
                            <div class="flex justify-between">
                                <span>基准价格</span>
                                <span class="status-value" id="base-price">--</span>
                            </div>
                            <div class="flex justify-between">
                                <span>市场趋势</span>
                                <span class="status-value" id="market-trend">--</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2 class="text-lg font-semibold mb-4">网格参数</h2>
                        <div class="space-y-2">
                            <div class="flex justify-between">
                                <span>网格大小</span>
                                <span class="status-value" id="grid-size">--</span>
                            </div>
                            <div class="flex justify-between">
                                <span>触发阈值</span>
                                <span class="status-value" id="threshold">--</span>
                            </div>
                            <div class="flex justify-between">
                                <span>下次委托金额</span>
                                <span class="status-value" id="next-order-amount">--</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2 class="text-lg font-semibold mb-4">资金状况</h2>
                        <div class="space-y-2">
                            <div class="flex justify-between">
                                <span>总资产(USDT)</span>
                                <span class="status-value" id="total-assets">--</span>
                            </div>
                            <div class="flex justify-between">
                                <span>USDT余额</span>
                                <span class="status-value" id="usdt-balance">--</span>
                            </div>
                            <div class="flex justify-between">
                                <span>BNB余额</span>
                                <span class="status-value" id="bnb-balance">--</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 系统资源监控 -->
                <div class="card mb-8">
                    <h2 class="text-lg font-semibold mb-4">系统资源</h2>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">CPU使用率</div>
                            <div class="text-2xl font-bold mt-1">{system_stats['cpu_percent']}%</div>
                        </div>
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">内存使用</div>
                            <div class="text-2xl font-bold mt-1">{system_stats['memory_percent']}%</div>
                            <div class="text-sm text-gray-500">
                                {system_stats['memory_used']}GB / {system_stats['memory_total']}GB
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 最近交易记录 -->
                <div class="card mt-4 mb-8">
                    <h2 class="text-lg font-semibold mb-4">最近交易</h2>
                    <div class="overflow-x-auto">
                        <table class="min-w-full">
                            <thead>
                                <tr class="border-b">
                                    <th class="text-left py-2">时间</th>
                                    <th class="text-left py-2">方向</th>
                                    <th class="text-left py-2">价格</th>
                                    <th class="text-left py-2">数量</th>
                                    <th class="text-left py-2">金额(USDT)</th>
                                </tr>
                            </thead>
                            <tbody id="trade-history">
                                <!-- 交易记录将通过JavaScript动态插入 -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- IP访问记录 -->
                <div class="card mb-8">
                    <h2 class="text-lg font-semibold mb-4">访问记录</h2>
                    <div class="overflow-x-auto">
                        <table class="min-w-full">
                            <thead>
                                <tr class="bg-gray-50">
                                    <th class="px-6 py-3 text-left">时间</th>
                                    <th class="px-6 py-3 text-left">IP地址</th>
                                    <th class="px-6 py-3 text-left">访问路径</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f'''
                                <tr class="border-b">
                                    <td class="px-6 py-4">{record["time"]}</td>
                                    <td class="px-6 py-4">{record["ip"]}</td>
                                    <td class="px-6 py-4">{record["path"]}</td>
                                </tr>
                                ''' for record in reversed(request.app['ip_logger'].get_records())])}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 系统日志 -->
                <div class="card">
                    <h2 class="text-lg font-semibold mb-4">系统日志</h2>
                    <div class="log-container" id="log-content">
                        <pre>{content}</pre>
                    </div>
                </div>
            </div>

            <script>
                async function updateStatus() {{
                    try {{
                        const response = await fetch('/api/status');
                        const data = await response.json();
                        
                        if (data.error) {{
                            console.error('获取状态失败:', data.error);
                            return;
                        }}
                        
                        // 更新基本信息
                        document.querySelector('#base-price').textContent = 
                            data.base_price.toFixed(2) + ' USDT';
                        
                        // 更新网格参数
                        document.querySelector('#grid-size').textContent = 
                            (data.grid_size * 100).toFixed(2) + '%';
                        document.querySelector('#threshold').textContent = 
                            (data.threshold * 100).toFixed(2) + '%';
                        
                        // 更新资金状况
                        document.querySelector('#total-assets').textContent = 
                            data.total_assets.toFixed(2) + ' USDT';
                        document.querySelector('#usdt-balance').textContent = 
                            data.usdt_balance.toFixed(2);
                        document.querySelector('#bnb-balance').textContent = 
                            data.bnb_balance.toFixed(4);
                        
                        // 更新交易历史
                        document.querySelector('#trade-history').innerHTML = data.trade_history.map(function(trade) {{ return `
                            <tr class="border-b">
                                <td class="py-2">${{trade.timestamp}}</td>
                                <td class="py-2 ${{trade.side === 'buy' ? 'text-green-500' : 'text-red-500'}}">
                                    ${{trade.side === 'buy' ? '买入' : '卖出'}}
                                </td>
                                <td class="py-2">${{parseFloat(trade.price).toFixed(2)}}</td>
                                <td class="py-2">${{parseFloat(trade.amount).toFixed(4)}}</td>
                                <td class="py-2">${{(parseFloat(trade.price) * parseFloat(trade.amount)).toFixed(2)}}</td>
                            </tr>
                        `; }}).join('');
                        
                        // 更新市场趋势
                        document.querySelector('#market-trend').textContent = data.market_trend;
                        
                        // 更新下次委托金额
                        const nextOrderAmount = `买入: ${{data.next_buy_amount.toFixed(2)}} USDT\n卖出: ${{data.next_sell_amount.toFixed(2)}} USDT`;
                        document.querySelector('#next-order-amount').textContent = nextOrderAmount;
                        
                        // 根据趋势设置颜色
                        const trendElement = document.querySelector('#market-trend');
                        trendElement.className = 'status-value ' + 
                            (data.market_trend.includes('上涨') ? 'text-green-500' : 
                             data.market_trend.includes('下跌') ? 'text-red-500' : 
                             'text-gray-500');
                        
                        console.log('状态更新成功:', data);
                    }} catch (error) {{
                        console.error('更新状态失败:', error);
                    }}
                }}

                // 每2秒更新一次状态
                setInterval(updateStatus, 2000);
                
                // 页面加载时立即更新一次
                updateStatus();
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_status(request):
    """处理状态API请求"""
    try:
        # 获取交易所数据
        balance = await request.app['trader'].exchange.fetch_balance()
        current_price = await request.app['trader']._get_latest_price()
        
        # 获取理财账户余额
        funding_balance = await request.app['trader'].exchange.fetch_funding_balance()
        
        # 获取网格参数
        grid_size = request.app['trader'].grid_size
        grid_size_decimal = grid_size / 100
        threshold = grid_size_decimal / 5
        
        # 计算总资产
        bnb_balance = float(balance['total'].get('BNB', 0))
        usdt_balance = float(balance['total'].get('USDT', 0))
        total_assets = usdt_balance + (bnb_balance * current_price)
        
        # 获取最近交易信息
        last_trade_price = request.app['trader'].last_trade_price
        last_trade_time = request.app['trader'].last_trade_time
        last_trade_time_str = datetime.fromtimestamp(last_trade_time).strftime('%Y-%m-%d %H:%M:%S') if last_trade_time else '--'
        
        # 获取交易历史
        trade_history = []
        if hasattr(request.app['trader'], 'order_tracker'):
            trades = request.app['trader'].order_tracker.get_trade_history()
            trade_history = [{
                'timestamp': datetime.fromtimestamp(trade['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                'side': trade.get('side', '--'),
                'price': trade.get('price', 0),
                'amount': trade.get('amount', 0),
                'profit': trade.get('profit', 0)
            } for trade in trades[-10:]]  # 只取最近10笔交易
        
        # 获取市场趋势
        trend = 'neutral'  # 默认为震荡
        if hasattr(request.app['trader'], 'trend_analyzer'):
            trend = await request.app['trader'].trend_analyzer.analyze_trend()
        
        trend_text = {
            'strong_uptrend': '强上涨',
            'weak_uptrend': '弱上涨',
            'strong_downtrend': '强下跌',
            'weak_downtrend': '弱下跌',
            'neutral': '震荡'
        }.get(trend, '震荡')
        
        # 计算下次委托金额
        next_buy_amount = await request.app['trader']._calculate_order_amount('buy')
        next_sell_amount = await request.app['trader']._calculate_order_amount('sell')
        
        # 构建响应数据
        status = {
            "base_price": request.app['trader'].base_price,
            "current_price": current_price,
            "grid_size": grid_size_decimal,
            "threshold": threshold,
            "total_assets": total_assets,
            "usdt_balance": usdt_balance,
            "bnb_balance": bnb_balance,
            "market_trend": trend_text,
            "next_buy_amount": next_buy_amount,
            "next_sell_amount": next_sell_amount,
            "trade_history": trade_history or []
        }
        
        return web.json_response(status)
    except Exception as e:
        logging.error(f"获取状态数据失败: {str(e)}")
        return web.json_response({"error": str(e)}, status=500)

async def start_web_server(trader):
    app = web.Application()
    # 添加中间件处理无效请求
    @web.middleware
    async def error_middleware(request, handler):
        try:
            return await handler(request)
        except web.HTTPException as ex:
            return web.json_response(
                {"error": str(ex)},
                status=ex.status,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        except Exception as e:
            return web.json_response(
                {"error": "Internal Server Error"},
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
    
    app.middlewares.append(error_middleware)
    app['trader'] = trader
    app['ip_logger'] = IPLogger()
    
    # 禁用访问日志
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
    
    app.router.add_get('/', handle_log)
    app.router.add_get('/api/logs', handle_log_content)
    app.router.add_get('/api/status', handle_status)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 58181)
    await site.start()

    # 打印访问地址
    local_ip = "localhost"  # 或者使用实际IP
    logging.info(f"Web服务已启动:")
    logging.info(f"- 本地访问: http://{local_ip}:58181")
    logging.info(f"- 局域网访问: http://0.0.0.0:58181")

async def handle_log_content(request):
    """只返回日志内容的API端点"""
    try:
        log_path = os.path.join(LogConfig.LOG_DIR, 'trading_system.log')
        if not os.path.exists(log_path):
            return web.Response(text="", status=404)
            
        async with aiofiles.open(log_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            
        # 将日志按行分割并倒序排列
        lines = content.strip().split('\n')
        lines.reverse()
        content = '\n'.join(lines)
            
        return web.Response(text=content)
    except Exception as e:
        return web.Response(text="", status=500) 