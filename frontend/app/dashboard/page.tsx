'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import { 
  LogOut, Upload, MessageSquare, FileText, Send, 
  Loader2, Table, Download, AlertCircle, Copy, BarChart3, Filter, AlertTriangle, Zap 
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{ 
    filename: string
    page: number
    text_preview?: string
    relevance_score?: number
    preview?: string
  }>
  structured_data?: any[]
  confidence?: 'high' | 'medium' | 'low' | 'error'
  chunks_found?: number
}

interface Document {
  document_id: string
  filename: string
  chunks_count: number
}

export default function DashboardPage() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'evaluation' | 'analytics'>('chat')
  const [evaluationResults, setEvaluationResults] = useState<any>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [analytics, setAnalytics] = useState<any>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<any>({})
  const [conflicts, setConflicts] = useState<any>(null)
  const [detectingConflicts, setDetectingConflicts] = useState(false)
  const [cacheStats, setCacheStats] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    if (!storedToken) {
      router.push('/login')
    } else {
      setToken(storedToken)
      loadDocuments(storedToken)
    }
  }, [router])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadDocuments = async (authToken: string) => {
    try {
      const response = await axios.get(`${API_URL}/documents/list`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      console.log('Loaded documents:', response.data.documents)
      setDocuments(response.data.documents)
      // Load cache stats too
      loadCacheStats()
    } catch (error: any) {
      console.error('Error loading documents:', error)
      if (error.response?.status === 401) {
        router.push('/login')
      } else {
        toast.error('Failed to load documents')
      }
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !token) return

    if (!file.name.endsWith('.pdf')) {
      toast.error('Only PDF files are supported')
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_URL}/documents/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        },
        timeout: 120000 // 2 minutes timeout for large files
      })
      toast.success(`Document uploaded: ${response.data.chunks_created} chunks created`)
      await loadDocuments(token)
    } catch (error: any) {
      console.error('Upload error:', error.response?.data)
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard!')
  }

  const loadAnalytics = async (authToken: string) => {
    try {
      const response = await axios.get(`${API_URL}/analytics`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      setAnalytics(response.data)
    } catch (error) {
      console.error('Analytics load error:', error)
    }
  }

  const downloadExport = async (type: 'door_schedule' | 'room_schedule') => {
    if (!token) return
    
    try {
      const response = await axios.get(`${API_URL}/export/${type}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${type}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success('Export downloaded!')
    } catch (error: any) {
      toast.error('Export failed')
    }
  }

  const detectConflicts = async () => {
    if (!token) return
    setDetectingConflicts(true)
    try {
      const response = await axios.get(`${API_URL}/detect-conflicts`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setConflicts(response.data)
      if (response.data.conflicts_found > 0) {
        toast.success(`Found ${response.data.conflicts_found} potential conflicts`)
      } else {
        toast.success('No conflicts detected')
      }
    } catch (error: any) {
      toast.error('Conflict detection failed')
    } finally {
      setDetectingConflicts(false)
    }
  }

  const loadCacheStats = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/cache/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setCacheStats(response.data)
    } catch (error: any) {
      console.error('Failed to load cache stats')
    }
  }

  const clearCache = async () => {
    if (!token) return
    try {
      await axios.post(`${API_URL}/cache/clear`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Cache cleared successfully')
      loadCacheStats()
    } catch (error: any) {
      toast.error('Failed to clear cache')
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !token || loading) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post(
        `${API_URL}/chat`,
        { 
          message: input,
          conversation_id: conversationId,
          filters: Object.keys(filters).length > 0 ? filters : null
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer || 'No response received',
        sources: response.data.sources?.map((s: any) => ({
          filename: s.filename || 'Unknown',
          page: s.page_number || s.page || 0,
          relevance_score: s.relevance_score || 0,
          preview: s.preview || ''
        })) || [],
        structured_data: response.data.structured_data || [],
        confidence: response.data.confidence || 'unknown',
        chunks_found: response.data.chunks_found || 0
      }

      setMessages(prev => [...prev, assistantMessage])
      setConversationId(response.data.conversation_id)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send message')
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const runEvaluation = async () => {
    if (!token) return
    setLoading(true)

    try {
      const response = await axios.get(`${API_URL}/evaluate`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setEvaluationResults(response.data)
      toast.success('Evaluation completed')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Evaluation failed')
    } finally {
      setLoading(false)
    }
  }

  const exportStructuredData = (data: any[]) => {
    const jsonStr = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'extracted_data.json'
    a.click()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary-600">
            Constructure AI - Project Brain
          </h1>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-red-600 transition-colors"
          >
            <LogOut className="h-5 w-5" />
            Logout
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        <div className="flex gap-2 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'chat'
                ? 'text-orange-600 border-b-2 border-orange-500'
                : 'text-gray-600 hover:text-orange-600'
            }`}
          >
            <MessageSquare className="inline h-5 w-5 mr-2" />
            Chat
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'documents'
                ? 'text-orange-600 border-b-2 border-orange-500'
                : 'text-gray-600 hover:text-orange-600'
            }`}
          >
            <FileText className="inline h-5 w-5 mr-2" />
            Documents ({documents.length})
          </button>
          <button
            onClick={() => setActiveTab('evaluation')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'evaluation'
                ? 'text-orange-600 border-b-2 border-orange-500'
                : 'text-gray-600 hover:text-orange-600'
            }`}
          >
            <Table className="inline h-5 w-5 mr-2" />
            Evaluation
          </button>
          <button
            onClick={() => { setActiveTab('analytics'); if (token) loadAnalytics(token); }}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'analytics'
                ? 'text-orange-600 border-b-2 border-orange-500'
                : 'text-gray-600 hover:text-orange-600'
            }`}
          >
            <BarChart3 className="inline h-5 w-5 mr-2" />
            Analytics
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'chat' && (
          <div className="bg-white rounded-xl shadow-lg h-[calc(100vh-220px)] flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 mt-12">
                  <MessageSquare className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium">Start a conversation</p>
                  <p className="text-sm mt-2">Ask questions about your construction documents</p>
                  <div className="mt-6 space-y-2 text-sm text-left max-w-md mx-auto bg-gray-50 p-4 rounded-lg">
                    <p className="font-medium text-gray-700">Try asking:</p>
                    <ul className="list-disc list-inside space-y-1 text-gray-600">
                      <li>What is the fire rating for corridor partitions?</li>
                      <li>Generate a door schedule</li>
                      <li>What flooring materials are specified?</li>
                    </ul>
                  </div>
                </div>
              )}

              {messages.map((message, idx) => (
                <div key={idx} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-orange-500 to-orange-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    {message.role === 'assistant' && (
                      <div className="flex justify-end mb-2">
                        <button
                          onClick={() => copyToClipboard(message.content)}
                          className="text-xs flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-200 transition-colors"
                          title="Copy to clipboard"
                        >
                          <Copy className="h-3 w-3" />
                          Copy
                        </button>
                      </div>
                    )}
                    <ReactMarkdown className="prose prose-sm max-w-none">
                      {message.content || 'No response'}
                    </ReactMarkdown>

                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-300">
                        <div className="flex items-center gap-2 mb-2">
                          <p className="font-semibold text-xs">📚 Sources</p>
                          {message.confidence && (
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              message.confidence === 'high' ? 'bg-green-100 text-green-700' :
                              message.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-200 text-gray-600'
                            }`}>
                              {message.confidence} confidence
                            </span>
                          )}
                        </div>
                        <div className="space-y-2">
                          {message.sources.map((source, i) => (
                            <div key={i} className="bg-white bg-opacity-50 rounded p-2 text-xs">
                              <div className="flex items-start justify-between gap-2 mb-1">
                                <div className="flex-1">
                                  <span className="font-semibold text-gray-800">📄 {source.filename}</span>
                                  <span className="text-gray-600 ml-2">Page {source.page}</span>
                                </div>
                                {source.relevance_score !== undefined && (
                                  <span className="text-xs text-gray-500 whitespace-nowrap">
                                    {(source.relevance_score * 100).toFixed(0)}% match
                                  </span>
                                )}
                              </div>
                              {source.preview && (
                                <p className="text-gray-600 text-xs mt-1 italic line-clamp-2">
                                  "{source.preview}"
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {message.structured_data && message.structured_data.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-300">
                        <div className="flex justify-between items-center mb-2">
                          <p className="font-semibold text-sm">Structured Data</p>
                          <div className="flex gap-2">
                            <button
                              onClick={() => downloadExport('door_schedule')}
                              className="text-xs flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors"
                              title="Export as Excel"
                            >
                              <Download className="h-3 w-3" />
                              Excel
                            </button>
                            <button
                              onClick={() => exportStructuredData(message.structured_data!)}
                              className="text-xs flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                            >
                              <Download className="h-3 w-3" />
                              JSON
                            </button>
                          </div>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs">
                            <thead>
                              <tr className="bg-gray-200">
                                {Object.keys(message.structured_data[0]).map(key => (
                                  <th key={key} className="px-2 py-1 text-left font-medium">
                                    {key ? key.replace(/_/g, ' ').toUpperCase() : 'N/A'}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {message.structured_data.slice(0, 10).map((row, i) => (
                                <tr key={i} className="border-b border-gray-200">
                                  {Object.values(row).map((val: any, j) => (
                                    <td key={j} className="px-2 py-1">
                                      {val?.toString() || 'N/A'}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {message.structured_data.length > 10 && (
                            <p className="text-xs text-gray-600 mt-2">
                              Showing 10 of {message.structured_data.length} items
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg px-4 py-3">
                    <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Filters and Input */}
            <div className="border-t p-4">
              {/* Conflict Detection */}
              {conflicts && conflicts.conflicts_found > 0 && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                    <div className="flex-1">
                      <h4 className="font-semibold text-red-900 mb-2">
                        {conflicts.conflicts_found} Potential Conflicts Detected
                      </h4>
                      <div className="space-y-3 text-sm">
                        {conflicts.conflicts.map((conflict: any, idx: number) => (
                          <div key={idx} className="bg-white p-3 rounded border border-red-200">
                            <p className="font-medium text-red-800 mb-1">📍 {conflict.topic}</p>
                            <p className="text-gray-700 mb-2">{conflict.potential_conflict}</p>
                            <div className="flex flex-wrap gap-2">
                              {conflict.sources.map((source: any, sidx: number) => (
                                <span key={sidx} className="text-xs px-2 py-1 bg-gray-100 rounded">
                                  {source.filename} (p.{source.page})
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    <button
                      onClick={() => setConflicts(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="mb-3 flex gap-2">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="text-sm flex items-center gap-2 px-3 py-1.5 rounded-md border border-orange-300 bg-orange-50 text-orange-700 hover:bg-orange-100 transition-colors"
                >
                  <Filter className="h-4 w-4" />
                  {showFilters ? 'Hide Filters' : 'Show Filters'}
                  {Object.keys(filters).length > 0 && (
                    <span className="ml-1 px-2 py-0.5 bg-orange-600 text-white rounded-full text-xs font-medium">
                      {Object.keys(filters).length}
                    </span>
                  )}
                </button>
                <button
                  onClick={detectConflicts}
                  disabled={detectingConflicts || documents.length === 0}
                  className="text-sm flex items-center gap-2 px-3 py-1.5 rounded-md border border-orange-300 bg-orange-50 text-orange-700 hover:bg-orange-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <AlertTriangle className="h-4 w-4" />
                  {detectingConflicts ? 'Detecting...' : 'Detect Conflicts'}
                </button>
              </div>

              {/* Filters Panel */}
              {showFilters && (
                <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Document Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Document</label>
                      <select
                        value={filters.document || ''}
                        onChange={(e) => {
                          const newFilters = { ...filters };
                          if (e.target.value) newFilters.document = e.target.value;
                          else delete newFilters.document;
                          setFilters(newFilters);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      >
                        <option value="">All Documents</option>
                        {documents.map(doc => (
                          <option key={doc.document_id} value={doc.filename}>{doc.filename}</option>
                        ))}
                      </select>
                    </div>

                    {/* Page Range Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Page Range</label>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          placeholder="Min"
                          value={filters.page_min || ''}
                          onChange={(e) => {
                            const newFilters = { ...filters };
                            if (e.target.value) newFilters.page_min = parseInt(e.target.value);
                            else delete newFilters.page_min;
                            setFilters(newFilters);
                          }}
                          className="w-1/2 px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                        <input
                          type="number"
                          placeholder="Max"
                          value={filters.page_max || ''}
                          onChange={(e) => {
                            const newFilters = { ...filters };
                            if (e.target.value) newFilters.page_max = parseInt(e.target.value);
                            else delete newFilters.page_max;
                            setFilters(newFilters);
                          }}
                          className="w-1/2 px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                      </div>
                    </div>

                    {/* Confidence Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Min Confidence</label>
                      <select
                        value={filters.min_confidence || ''}
                        onChange={(e) => {
                          const newFilters = { ...filters };
                          if (e.target.value) newFilters.min_confidence = parseFloat(e.target.value);
                          else delete newFilters.min_confidence;
                          setFilters(newFilters);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      >
                        <option value="">Any</option>
                        <option value="0.8">High (80%+)</option>
                        <option value="0.6">Medium (60%+)</option>
                        <option value="0.4">Low (40%+)</option>
                      </select>
                    </div>
                  </div>
                  
                  {Object.keys(filters).length > 0 && (
                    <button
                      onClick={() => setFilters({})}
                      className="mt-3 text-sm text-red-600 hover:text-red-700 font-medium"
                    >
                      Clear All Filters
                    </button>
                  )}
                </div>
              )}

              <form onSubmit={handleSendMessage} className="flex gap-2">
                <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question about your project..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent text-gray-900 bg-white"
                  disabled={loading || documents.length === 0}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim() || documents.length === 0}
                  className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="h-5 w-5" />
                  Send
                </button>
              </form>
            </div>

            {documents.length === 0 && (
              <div className="p-4 bg-yellow-50 border-t border-yellow-200 flex items-center gap-2 text-yellow-800">
                <AlertCircle className="h-5 w-5" />
                <span className="text-sm">Please upload documents first to start chatting</span>
              </div>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">Documents</h2>
              <label className="cursor-pointer">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={uploading}
                />
                <div className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                  {uploading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Upload className="h-5 w-5" />
                  )}
                  {uploading ? 'Uploading...' : 'Upload PDF'}
                </div>
              </label>
            </div>

            {documents.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">No documents uploaded</p>
                <p className="text-sm mt-2">Upload construction documents to get started</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {documents.map((doc) => (
                  <div key={doc.document_id} className="border border-gray-200 rounded-lg p-4 hover:border-orange-300 hover:shadow-md transition-all">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <FileText className="h-8 w-8 text-orange-600 mt-1" />
                        <div>
                          <h3 className="font-medium text-gray-900">{doc.filename}</h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {doc.chunks_count} chunks indexed
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'evaluation' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">System Evaluation</h2>
              <button
                onClick={runEvaluation}
                disabled={loading || documents.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg hover:from-orange-600 hover:to-orange-700 transition-all shadow-md disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Table className="h-5 w-5" />
                )}
                Run Evaluation
              </button>
            </div>

            {evaluationResults ? (
              <div>
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm text-green-600 font-medium">Correct</p>
                    <p className="text-2xl font-bold text-green-700">{evaluationResults.summary.correct}</p>
                  </div>
                  <div className="bg-yellow-50 p-4 rounded-lg">
                    <p className="text-sm text-yellow-600 font-medium">Partially Correct</p>
                    <p className="text-2xl font-bold text-yellow-700">{evaluationResults.summary.partially_correct}</p>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg">
                    <p className="text-sm text-red-600 font-medium">Incorrect</p>
                    <p className="text-2xl font-bold text-red-700">{evaluationResults.summary.incorrect}</p>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-blue-600 font-medium">With Sources</p>
                    <p className="text-2xl font-bold text-blue-700">{evaluationResults.summary.total_with_sources}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {evaluationResults.results.map((result: any, idx: number) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-medium text-gray-900">{result.query}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          result.correctness === 'correct' ? 'bg-green-100 text-green-800' :
                          result.correctness === 'partially_correct' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {result.correctness ? result.correctness.replace('_', ' ') : 'unknown'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{result.answer}</p>
                      <div className="flex gap-4 text-xs text-gray-500">
                        <span>Category: {result.category}</span>
                        <span>Sources: {result.sources_count}</span>
                        <span>Keyword Score: {result.keyword_score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Table className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">No evaluation results yet</p>
                <p className="text-sm mt-2">Run evaluation to test the RAG system</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">Query Analytics & Cache</h2>
              <button
                onClick={clearCache}
                className="text-sm px-3 py-1.5 bg-red-50 text-red-600 rounded-md border border-red-200 hover:bg-red-100 transition-colors"
              >
                Clear Cache
              </button>
            </div>

            {analytics ? (
              <div className="space-y-6">
                {/* Summary Stats */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                    <p className="text-sm text-orange-600 font-medium">Total Queries</p>
                    <p className="text-2xl font-bold text-orange-700">{analytics.recent_queries?.length || 0}</p>
                  </div>
                  <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                    <p className="text-sm text-orange-600 font-medium">Avg Sources</p>
                    <p className="text-2xl font-bold text-orange-700">{analytics.avg_sources_per_query?.toFixed(1) || 0}</p>
                  </div>
                  <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                    <p className="text-sm text-orange-600 font-medium">Documents Used</p>
                    <p className="text-2xl font-bold text-orange-700">{analytics.document_usage?.length || 0}</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <p className="text-sm text-green-600 font-medium">Cache Hits</p>
                    <p className="text-2xl font-bold text-green-700">{cacheStats?.valid_cache_entries || 0}</p>
                  </div>
                </div>

                {/* Cache Stats */}
                {cacheStats && (
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                      <Zap className="h-5 w-5" />
                      Cache Performance
                    </h3>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-green-600">Total Cached</p>
                        <p className="text-lg font-bold text-green-700">{cacheStats.total_cached_queries}</p>
                      </div>
                      <div>
                        <p className="text-green-600">Valid Entries</p>
                        <p className="text-lg font-bold text-green-700">{cacheStats.valid_cache_entries}</p>
                      </div>
                      <div>
                        <p className="text-green-600">Cache TTL</p>
                        <p className="text-lg font-bold text-green-700">{(cacheStats.cache_ttl_seconds / 60).toFixed(0)} min</p>
                      </div>
                    </div>
                  </div>
                )}


                {/* Popular Queries */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Popular Queries</h3>
                  <div className="space-y-2">
                    {analytics.popular_queries?.slice(0, 10).map((item: any, idx: number) => (
                      <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="text-sm text-gray-700">{item.query}</span>
                        <span className="text-xs font-medium text-gray-500 px-2 py-1 bg-white rounded">
                          {item.count}x
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Document Usage */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Document Usage</h3>
                  <div className="space-y-2">
                    {Array.isArray(analytics.document_usage) ? (
                      analytics.document_usage.map((item: any, idx: number) => (
                        <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                          <span className="text-sm text-gray-700">{item.document}</span>
                          <div className="flex items-center gap-2">
                            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-gradient-to-r from-orange-500 to-orange-600 rounded-full"
                                style={{ width: `${(item.count / analytics.recent_queries.length) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs font-medium text-gray-500 w-8 text-right">
                              {item.count}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">No document usage data yet</p>
                    )}
                  </div>
                </div>

                {/* Recent Queries */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Recent Queries</h3>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {analytics.recent_queries?.slice(0, 20).map((item: any, idx: number) => (
                      <div key={idx} className="p-3 border border-gray-200 rounded-lg">
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-sm text-gray-700 font-medium">{item.query}</span>
                          <span className="text-xs text-gray-500">
                            {new Date(item.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="flex gap-3 text-xs text-gray-500">
                          {item.sources_count !== undefined && (
                            <span>{item.sources_count} sources</span>
                          )}
                          {item.confidence && (
                            <span className={`px-2 py-0.5 rounded-full ${
                              item.confidence === 'high' ? 'bg-green-100 text-green-700' :
                              item.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-200 text-gray-600'
                            }`}>
                              {item.confidence}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <BarChart3 className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">No analytics data yet</p>
                <p className="text-sm mt-2">Start asking questions to see analytics</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
