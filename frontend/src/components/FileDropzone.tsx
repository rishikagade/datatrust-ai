import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { api } from '../api/client'

const steps = ['Upload received', 'Profiling columns', 'Running rules', 'Scoring audit', 'Writing AI report']

export default function FileDropzone({ onResult }: { onResult: (r: any) => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(false)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [stepIndex, setStepIndex] = useState(0)

  const uploadFile = async (file: File) => {
    setError(false)
    setSelectedFile(file.name)
    setBusy(true)
    setStepIndex(0)
    const timer = window.setInterval(() => setStepIndex((current) => Math.min(current + 1, steps.length - 1)), 600)
    try {
      const json = await api.audit(file)
      onResult(json)
    } catch {
      setError(true)
    } finally {
      window.clearInterval(timer)
      setBusy(false)
    }
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles[0]) uploadFile(acceptedFiles[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv', '.tsv'] },
    maxFiles: 1,
  })

  return (
    <div className="max-w-3xl">
      <div {...getRootProps()} className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition ${isDragActive ? 'border-teal-500 bg-teal-50' : 'border-stone-300 bg-white hover:border-teal-300 hover:bg-stone-50'}`}>
        <input {...getInputProps()} disabled={busy} />
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-teal-50 text-2xl text-teal-800">↑</div>
        <p className="mt-4 text-base font-semibold text-slate-800">{isDragActive ? 'Drop the file to start the audit' : 'Drag and drop your CSV here'}</p>
        <p className="mt-2 text-sm text-slate-500">or click to browse. Supported formats: .csv and .tsv</p>
      </div>

      {selectedFile ? <p className="mt-3 text-sm text-slate-700">Selected file: <strong>{selectedFile}</strong></p> : null}

      {busy ? (
        <div className="mt-4 rounded-lg border border-teal-200 bg-teal-50 p-4">
          <p className="text-sm font-semibold text-teal-950">Auditing dataset...</p>
          <div className="mt-3 grid gap-2">
            {steps.map((step, index) => (
              <div key={step} className="flex items-center gap-2 text-sm">
                <span className={`h-2.5 w-2.5 rounded-full ${index <= stepIndex ? 'bg-teal-700' : 'bg-stone-300'}`} />
                <span className={index <= stepIndex ? 'text-teal-950' : 'text-slate-500'}>{step}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Upload failed. Check that the file is a valid CSV or TSV and try again.
        </div>
      ) : null}
    </div>
  )
}
