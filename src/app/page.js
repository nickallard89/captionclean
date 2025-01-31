'use client'

import { useState } from 'react'

export default function Home() {
  const [charLimit, setCharLimit] = useState(42)
  const [file, setFile] = useState(null)
  const [processing, setProcessing] = useState(false)

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0]
    if (selectedFile && (selectedFile.name.endsWith('.srt') || selectedFile.name.endsWith('.txt'))) {
      setFile(selectedFile)
    } else {
      alert('Please select an SRT or TXT file')
    }
  }

  const processFile = async () => {
  if (!file) return

  setProcessing(true)
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('charLimit', charLimit)

    console.log('Sending request to backend...')
    const response = await fetch('http://127.0.0.1:5000/process-srt', {
      method: 'POST',
      body: formData,
    })

    console.log('Response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Server error: ${response.status} - ${errorText}`)
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = file.name.replace(/\.(srt|txt)$/, '_cleaned$&')
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

  } catch (error) {
    console.error('Detailed error:', error)
    alert('Error processing file: ' + error.message)
  } finally {
    setProcessing(false)
  }
}

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-4xl font-bold mb-8 text-center text-gray-800">
          Caption Clean
        </h1>
        
        <div className="space-y-6">
          <div>
            <label className="block text-gray-700 font-medium mb-2">Character Limit</label>
            <input
              type="number"
              value={charLimit}
              onChange={(e) => {
                const value = e.target.value;
                setCharLimit(value === '' ? '' : Number(value));
              }}
              className="w-32 p-2 border border-gray-300 rounded-md 
                focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none
                text-gray-900 text-base"
              min="1"
              inputMode="numeric"
            />
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-2">Upload File</label>
            <input
              type="file"
              accept=".srt,.txt"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-indigo-50 file:text-indigo-600
                hover:file:bg-indigo-100
                cursor-pointer"
            />
          </div>

          <button 
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 px-4 rounded-md
              transition-colors duration-200 ease-in-out
              disabled:opacity-50 disabled:cursor-not-allowed
              shadow-sm"
            onClick={processFile}
            disabled={!file || processing}
          >
            {processing ? 'Processing...' : 'Process File'}
          </button>
        </div>

        <p className="mt-6 text-sm text-gray-600 text-center">
          Upload an SRT or TXT file and adjust the character limit to balance your subtitles.
        </p>
      </div>
    </div>
  )
}