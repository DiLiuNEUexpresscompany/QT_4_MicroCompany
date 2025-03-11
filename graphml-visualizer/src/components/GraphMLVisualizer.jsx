import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';

const GraphMLVisualizer = () => {
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterWeight, setFilterWeight] = useState(0);
  const [nodeLimit, setNodeLimit] = useState(100);
  const [layoutRunning, setLayoutRunning] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [detailsVisible, setDetailsVisible] = useState(true);
  const svgRef = useRef(null);
  const fileInputRef = useRef(null);

  // Sample nodes data
  const sampleNodes = [
    {
      id: 'AAPL',
      description:
        'Apple is among the largest companies in the world, with a broad portfolio of hardware and software products targeted at consumers and businesses.',
      sic_code: '3571.0',
      market_cap: '3394402637153.0',
      market_cap_value: 3394402637153.0,
      market_cap_formatted: '3.39万亿',
      source: 'nasdaq100',
    },
    {
      id: 'NVDA',
      description:
        'Nvidia Corp is an upfront developer of graphics processing unit and a full-stack computing infrastructure company with data-center-scale offerings that are reshaping industry.',
      sic_code: '3674.0',
      market_cap: '2630442000000.0',
      market_cap_value: 2630442000000.0,
      market_cap_formatted: '2.63万亿',
      source: 'nasdaq100',
    },
    {
      id: 'TSLA',
      description:
        'Tesla, Inc. designs, develops, manufactures, and sells electric vehicles and energy generation and storage systems.',
      sic_code: '3711.0',
      market_cap: '774801000000.0',
      market_cap_value: 774801000000.0,
      market_cap_formatted: '774.80十亿',
      source: 'nasdaq100',
    },
    {
      id: 'IMNM',
      description: 'Immunome Inc is a biopharmaceutical company.',
      sic_code: '2836.0',
      market_cap: '526310000.0',
      market_cap_value: 526310000.0,
      market_cap_formatted: '526.31百万',
      source: 'nasdaq',
    },
    {
      id: 'AGMH',
      description: 'AGM Group Holdings Inc provides financial technology services.',
      sic_code: '7389.0',
      market_cap: '25000000.0',
      market_cap_value: 25000000.0,
      market_cap_formatted: '25.00百万',
      source: 'nasdaq',
    },
    {
      id: 'OMI',
      description: 'Owens & Minor Inc is a healthcare logistics company.',
      sic_code: '5047.0',
      market_cap: '1200000000.0',
      market_cap_value: 1200000000.0,
      market_cap_formatted: '1.20十亿',
      source: 'nyse',
    },
  ];

  // Sample links data
  const sampleLinks = [
    {
      source: 'TSLA',
      target: 'IMNM',
      weight: 0.629,
    },
    {
      source: 'TSLA',
      target: 'AGMH',
      weight: 0.631,
    },
    {
      source: 'TSLA',
      target: 'OMI',
      weight: 0.632,
    },
    {
      source: 'AAPL',
      target: 'NVDA',
      weight: 0.745,
    },
  ];

  // Parse GraphML data
  const parseGraphML = (xmlString) => {
    setLoading(true);
    setError(null);

    try {
      // Clean and normalize XML string
      const cleanedXml = xmlString
        .replace(/\s+<edge/g, '<edge')
        .replace(/>\s+s\s+</g, '><')
        .replace(/>\s*s\s*<edge/g, '><edge');

      // Parse XML using DOMParser
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(cleanedXml, 'application/xml');

      // Check for parsing errors
      const parseError = xmlDoc.querySelector('parsererror');
      if (parseError) {
        console.error('XML parsing error, attempting manual processing...');

        // Manual node extraction
        const nodes = [];
        const nodeMatches = cleanedXml.match(/<node id="([^"]+)">([\s\S]*?)<\/node>/g);

        if (nodeMatches) {
          nodeMatches.forEach((nodeXml) => {
            const idMatch = nodeXml.match(/<node id="([^"]+)">/);
            if (idMatch && idMatch[1]) {
              const id = idMatch[1];
              const node = { id };

              // Extract description
              const descMatch = nodeXml.match(/<data key="d0">([\s\S]*?)<\/data>/);
              if (descMatch && descMatch[1]) {
                node.description = descMatch[1].trim();
              }

              // Extract SIC code
              const sicMatch = nodeXml.match(/<data key="d1">([\s\S]*?)<\/data>/);
              if (sicMatch && sicMatch[1]) {
                node.sic_code = sicMatch[1].trim();
              }

              // Extract market cap
              const mcapMatch = nodeXml.match(/<data key="d2">([\s\S]*?)<\/data>/);
              if (mcapMatch && mcapMatch[1]) {
                node.market_cap = mcapMatch[1].trim();
                node.market_cap_value = parseFloat(node.market_cap);
                node.market_cap_formatted = formatMarketCap(node.market_cap_value);
              }

              // Extract source
              const sourceMatch = nodeXml.match(/<data key="d3">([\s\S]*?)<\/data>/);
              if (sourceMatch && sourceMatch[1]) {
                node.source = sourceMatch[1].trim();
              }

              nodes.push(node);
            }
          });
        }

        // Extract edges
        const links = [];
        const edgeMatches = cleanedXml.match(/<edge source="([^"]+)" target="([^"]+)">([\s\S]*?)<\/edge>/g);

        if (edgeMatches) {
          edgeMatches.forEach((edgeXml) => {
            const sourceTargetMatch = edgeXml.match(/<edge source="([^"]+)" target="([^"]+)">/);
            if (sourceTargetMatch && sourceTargetMatch[1] && sourceTargetMatch[2]) {
              const source = sourceTargetMatch[1];
              const target = sourceTargetMatch[2];

              const link = { source, target, weight: 0 };

              // Extract weight
              const weightMatch = edgeXml.match(/<data key="d6">([\s\S]*?)<\/data>/);
              if (weightMatch && weightMatch[1]) {
                link.weight = parseFloat(weightMatch[1].trim());
              }

              links.push(link);
            }
          });
        }

        if (nodes.length === 0 && links.length === 0) {
          throw new Error('Failed to parse XML data');
        }

        // Filter data
        const filteredNodes = nodes.slice(0, nodeLimit);
        const nodeIds = new Set(filteredNodes.map((node) => node.id));
        const filteredLinks = links.filter(
          (link) => nodeIds.has(link.source) && nodeIds.has(link.target) && link.weight >= filterWeight
        );

        setGraph({
          nodes: filteredNodes,
          links: filteredLinks,
          allNodes: nodes,
          allLinks: links,
        });
      } else {
        // XML parsing successful, continue normal processing
        const nodeElements = xmlDoc.querySelectorAll('node');
        const nodes = Array.from(nodeElements).map((nodeEl) => {
          const id = nodeEl.getAttribute('id');
          const node = { id };
          const dataElements = nodeEl.querySelectorAll('data');

          dataElements.forEach((dataEl) => {
            const key = dataEl.getAttribute('key');
            // Possible mapping like <key id="d0" attr.name="description" ...>
            const keyName =
              xmlDoc.querySelector(`key[id="${key}"]`)?.getAttribute('attr.name') || key;
            node[keyName] = dataEl.textContent.trim();
          });

          if (node.market_cap) {
            node.market_cap_formatted = formatMarketCap(parseFloat(node.market_cap));
            node.market_cap_value = parseFloat(node.market_cap);
          }

          return node;
        });

        const edgeElements = xmlDoc.querySelectorAll('edge');
        const links = Array.from(edgeElements).map((edgeEl) => {
          const source = edgeEl.getAttribute('source');
          const target = edgeEl.getAttribute('target');

          const link = { source, target, weight: 0 };
          const dataElements = edgeEl.querySelectorAll('data');

          dataElements.forEach((dataEl) => {
            const key = dataEl.getAttribute('key');
            const keyName =
              xmlDoc.querySelector(`key[id="${key}"]`)?.getAttribute('attr.name') || key;
            const value = dataEl.textContent.trim();
            link[keyName] = keyName === 'weight' ? parseFloat(value) : value;
          });

          return link;
        });

        // Filter data
        const filteredNodes = nodes.slice(0, nodeLimit);
        const nodeIds = new Set(filteredNodes.map((n) => n.id));
        const filteredLinks = links.filter(
          (link) => nodeIds.has(link.source) && nodeIds.has(link.target) && link.weight >= filterWeight
        );

        setGraph({
          nodes: filteredNodes,
          links: filteredLinks,
          allNodes: nodes,
          allLinks: links,
        });
      }
    } catch (err) {
      console.error('Error parsing GraphML:', err);
      setError('Error parsing GraphML: ' + err.message);
      // Use sample data on parsing failure
      loadSampleData();
    } finally {
      setLoading(false);
    }
  };

  // Format market cap
  const formatMarketCap = (value) => {
    if (value >= 1e12) {
      return (value / 1e12).toFixed(2) + '万亿';
    } else if (value >= 1e9) {
      return (value / 1e9).toFixed(2) + '十亿';
    } else if (value >= 1e6) {
      return (value / 1e6).toFixed(2) + '百万';
    } else {
      return value.toFixed(2);
    }
  };

  // Handle file upload
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      parseGraphML(content);
    };
    reader.onerror = (e) => {
      setError('Error reading file: ' + e.target.error);
    };
    reader.readAsText(file);
  };

  // Handle sample data loading
  const loadSampleData = () => {
    setGraph({
      nodes: sampleNodes,
      links: sampleLinks,
      allNodes: sampleNodes,
      allLinks: sampleLinks,
    });
  };

  // Render graph using D3.js
  const renderGraph = () => {
    if (!graph.nodes || graph.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Clear previous graph
    svg.selectAll('*').remove();

    // Create zoom behavior
    const zoom = d3
      .zoom()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create a group element to contain all graph elements
    const g = svg.append('g');

    // Create color scale based on market cap
    const marketCapValues = graph.nodes.filter((d) => d.market_cap_value).map((d) => d.market_cap_value);
    const color = d3
      .scaleSequential()
      .domain([d3.min(marketCapValues) || 0, d3.max(marketCapValues) || 1])
      .interpolator(d3.interpolateBlues);

    // Create force-directed layout
    const simulation = d3
      .forceSimulation(graph.nodes)
      .force(
        'link',
        d3.forceLink(graph.links).id((d) => d.id).distance(100)
      )
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('x', d3.forceX(width / 2).strength(0.1))
      .force('y', d3.forceY(height / 2).strength(0.1));

    // Draw edges
    const link = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(graph.links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d) => Math.max(1, d.weight * 3));

    // Create node groups
    const node = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graph.nodes)
      .enter()
      .append('g')
      .call(
        d3
          .drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
      );

    // Add circular nodes
    node
      .append('circle')
      .attr('r', (d) => calculateNodeSize(d))
      .attr('fill', (d) => (d.market_cap_value ? color(d.market_cap_value) : '#ccc'))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);

    // Add node labels
    node
      .append('text')
      .attr('dy', 4)
      .attr('dx', (d) => calculateNodeSize(d) + 5)
      .text((d) => d.id)
      .attr('font-size', '12px')
      .attr('fill', '#333');

    // Node mouse events
    node
      .on('mouseover', function (event, d) {
        d3.select(this).select('circle').attr('stroke', '#000').attr('stroke-width', 2);
        setSelectedNode(d);
      })
      .on('mouseout', function () {
        d3.select(this).select('circle').attr('stroke', '#fff').attr('stroke-width', 1.5);
      })
      .on('click', function (event, d) {
        setSelectedNode(d);
        setDetailsVisible(true); // Show details panel when a node is clicked
        event.stopPropagation();
      });

    // Click background to clear selected node
    svg.on('click', () => {
      setSelectedNode(null);
    });

    // Update layout
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    // Node dragging functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Set layout state
    setLayoutRunning(true);

    // Stop layout calculation after a time
    setTimeout(() => {
      simulation.alphaTarget(0);
      setLayoutRunning(false);
    }, 3000);
  };

  // Calculate node size based on market cap
  const calculateNodeSize = (node) => {
    if (!node.market_cap_value) return 5;
    const minSize = 5;
    const maxSize = 15;
    const minMarketCap = 1e6; // 1 million
    const maxMarketCap = 1e12; // 1 trillion

    // Logarithmic scale to handle the large range
    const normalized =
      (Math.log(node.market_cap_value) - Math.log(minMarketCap)) /
      (Math.log(maxMarketCap) - Math.log(minMarketCap));
    return minSize + normalized * (maxSize - minSize);
  };

  // Search and filter nodes
  const handleSearch = () => {
    if (!graph.allNodes) return;
    const term = searchTerm.toUpperCase();
    let matchedNodes = [];

    if (term) {
      matchedNodes = graph.allNodes.filter(
        (node) =>
          node.id.includes(term) ||
          (node.description && node.description.toUpperCase().includes(term))
      );
    } else {
      matchedNodes = graph.allNodes.slice(0, nodeLimit);
    }

    // Build node ID set
    const nodeIds = new Set(matchedNodes.map((node) => node.id));

    // Filter edges, keep those with at least one endpoint in matched nodes
    const matchedLinks = graph.allLinks.filter((link) => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      return (
        (nodeIds.has(sourceId) || nodeIds.has(targetId)) &&
        link.weight >= filterWeight
      );
    });

    // Get connected node IDs
    const connectedNodeIds = new Set();
    matchedLinks.forEach((link) => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      connectedNodeIds.add(sourceId);
      connectedNodeIds.add(targetId);
    });

    // Build final node set, including matched nodes and connected nodes
    const finalNodeIds = new Set([...nodeIds, ...connectedNodeIds]);
    const finalNodes = graph.allNodes.filter((node) => finalNodeIds.has(node.id));

    // Update graph data
    setGraph({
      ...graph,
      nodes: finalNodes,
      links: matchedLinks,
    });
  };

  // Handle weight filter change
  const handleWeightFilterChange = (value) => {
    setFilterWeight(value);
  };

  // Handle node limit change
  const handleNodeLimitChange = (value) => {
    setNodeLimit(value);
  };

  // Apply filters
  const applyFilters = () => {
    handleSearch();
  };

  // Toggle sidebars
  const toggleLeftSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  const toggleRightSidebar = () => {
    setDetailsVisible(!detailsVisible);
  };

  // Render graph when component mounts or graph data updates
  useEffect(() => {
    if (graph.nodes && graph.nodes.length > 0) {
      renderGraph();
    }
  }, [graph.nodes, graph.links]);

  // Load sample data on component mount
  useEffect(() => {
    loadSampleData();
  }, []);
  
  // Add resize handler
  useEffect(() => {
    const handleResize = () => {
      if (graph.nodes && graph.nodes.length > 0) {
        renderGraph();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [graph]);

  return (
    <div className="flex flex-col h-screen bg-gray-50" style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif' }}>
      {/* Top Navigation Bar */}
      <div className="bg-gray-800 text-white p-3 flex items-center justify-between shadow-md">
        <div className="flex items-center">
          <button
            onClick={toggleLeftSidebar}
            className="mr-3 p-1 rounded hover:bg-gray-700 transition"
            title={sidebarVisible ? "隐藏工具" : "显示工具"}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 className="text-xl font-bold">GraphML 可视化工具</h1>
        </div>
        <div className="flex items-center">
          <span className="mr-3 text-sm">
            节点: {graph.nodes?.length || 0} | 边: {graph.links?.length || 0}
          </span>
          <button
            onClick={() => fileInputRef.current.click()}
            className="px-3 py-1 bg-blue-500 rounded hover:bg-blue-600 transition mr-2 text-sm"
          >
            上传 GraphML
          </button>
          <button
            onClick={loadSampleData}
            className="px-3 py-1 bg-green-500 rounded hover:bg-green-600 transition text-sm"
          >
            示例数据
          </button>
          <input
            type="file"
            accept=".graphml,.xml"
            onChange={handleFileUpload}
            ref={fileInputRef}
            className="hidden"
          />
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Controls */}
        {sidebarVisible && (
          <div className="w-64 bg-white p-4 shadow-md overflow-y-auto transition-all">
            {/* Search Box */}
            <div className="mb-6">
              <label className="block mb-2 font-medium text-gray-700">搜索节点</label>
              <div className="flex">
                <input
                  type="text"
                  placeholder="节点ID或描述..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="px-3 py-2 border rounded-l flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSearch}
                  className="px-4 py-2 text-white bg-blue-500 rounded-r hover:bg-blue-600 transition"
                >
                  搜索
                </button>
              </div>
            </div>

            {/* Weight Filter */}
            <div className="mb-6">
              <label className="block mb-2 font-medium text-gray-700">
                最小权重: {filterWeight.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={filterWeight}
                onChange={(e) => handleWeightFilterChange(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0</span>
                <span>0.5</span>
                <span>1</span>
              </div>
            </div>

            {/* Node Limit */}
            <div className="mb-6">
              <label className="block mb-2 font-medium text-gray-700">节点限制</label>
              <select
                value={nodeLimit}
                onChange={(e) => handleNodeLimitChange(parseInt(e.target.value))}
                className="px-3 py-2 border rounded w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="200">200</option>
                <option value="500">500</option>
                <option value="1000">1000</option>
              </select>
            </div>

            <button
              onClick={applyFilters}
              className="w-full px-4 py-2 text-white bg-indigo-500 rounded hover:bg-indigo-600 transition mb-6"
            >
              应用过滤器
            </button>

            {/* Status Information */}
            {layoutRunning && (
              <div className="p-3 mb-4 bg-blue-50 text-blue-700 rounded flex items-center">
                <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                正在计算布局...
              </div>
            )}
            
            {loading && (
              <div className="p-3 mb-4 bg-blue-50 text-blue-700 rounded flex items-center">
                <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                加载中...
              </div>
            )}
            
            {error && (
              <div className="p-3 mb-4 bg-red-50 text-red-700 rounded">
                错误: {error}
              </div>
            )}

            {/* Legend */}
            <div className="border rounded p-3">
              <h3 className="font-medium text-gray-700 mb-2">图例</h3>
              <div className="flex items-center mb-2">
                <div className="w-4 h-4 rounded-full bg-blue-900 mr-2"></div>
                <span className="text-sm">大市值</span>
              </div>
              <div className="flex items-center mb-2">
                <div className="w-4 h-4 rounded-full bg-blue-500 mr-2"></div>
                <span className="text-sm">中等市值</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 rounded-full bg-blue-200 mr-2"></div>
                <span className="text-sm">小市值</span>
              </div>
            </div>
          </div>
        )}

        {/* Main Graph Area */}
        <div className="flex-1 relative">
          <svg ref={svgRef} width="100%" height="100%" className="bg-white"></svg>
          
          {/* Floating Status Message */}
          {layoutRunning && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-4 py-2 rounded-full shadow-lg">
              正在计算布局...
            </div>
          )}
          
          {/* Toggle Right Sidebar Button */}
          {selectedNode && !detailsVisible && (
            <button
              onClick={toggleRightSidebar}
              className="absolute top-4 right-4 bg-white p-2 rounded-full shadow-md hover:bg-gray-100 transition"
              title="显示详情"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
              </svg>
            </button>
          )}
        </div>

        {/* Right Sidebar - Node Details */}
        {selectedNode && detailsVisible && (
          <div className="w-80 bg-white p-5 shadow-md overflow-y-auto transition-all">
            {/* Node Title */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">{selectedNode.id}</h2>
              <button 
                onClick={toggleRightSidebar}
                className="text-gray-500 hover:text-gray-700" 
                title="关闭详情"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>

            {/* Description */}
            {selectedNode.description && (
              <div className="mb-6">
                <h3 className="text-gray-700 font-semibold mb-2">描述</h3>
                <p className="text-gray-600 text-sm bg-gray-50 p-3 rounded">{selectedNode.description}</p>
              </div>
            )}

            {/* Properties */}
            <div className="mb-6">
              <h3 className="text-gray-700 font-semibold mb-2">属性</h3>
              <div className="bg-gray-50 rounded overflow-hidden">
                {selectedNode.source && (
                  <div className="flex justify-between py-2 px-3 border-b border-gray-100">
                    <span className="text-gray-600">来源</span>
                    <span className="font-medium">{selectedNode.source}</span>
                  </div>
                )}

                {selectedNode.sic_code && (
                  <div className="flex justify-between py-2 px-3 border-b border-gray-100">
                    <span className="text-gray-600">SIC代码</span>
                    <span className="font-medium">{selectedNode.sic_code}</span>
                  </div>
                )}

                {selectedNode.market_cap_formatted && (
                  <div className="flex justify-between py-2 px-3">
                    <span className="text-gray-600">市值</span>
                    <span className="font-medium">{selectedNode.market_cap_formatted}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Connections */}
            <div>
              <h3 className="text-gray-700 font-semibold mb-2">连接</h3>
              <div className="bg-gray-50 rounded overflow-hidden">
                {graph.links
                  .filter(
                    (link) =>
                      (typeof link.source === 'object'
                        ? link.source.id === selectedNode.id
                        : link.source === selectedNode.id) ||
                      (typeof link.target === 'object'
                        ? link.target.id === selectedNode.id
                        : link.target === selectedNode.id)
                  )
                  .map((link, index) => {
                    const connectedNodeId =
                      (typeof link.source === 'object' ? link.source.id : link.source) ===
                      selectedNode.id
                        ? typeof link.target === 'object'
                          ? link.target.id
                          : link.target
                        : typeof link.source === 'object'
                        ? link.source.id
                        : link.source;

                    return (
                      <div key={index} className="flex justify-between items-center py-2 px-3 border-b border-gray-100 last:border-0">
                        <span className="font-medium">{connectedNodeId}</span>
                        <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          权重: {link.weight.toFixed(3)}
                        </span>
                      </div>
                    );
                  })}
                  
                {graph.links.filter(
                  (link) =>
                    (typeof link.source === 'object'
                      ? link.source.id === selectedNode.id
                      : link.source === selectedNode.id) ||
                    (typeof link.target === 'object'
                      ? link.target.id === selectedNode.id
                      : link.target === selectedNode.id)
                ).length === 0 && (
                  <div className="py-2 px-3 text-gray-500 italic text-sm">
                    没有符合条件的连接
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GraphMLVisualizer;
