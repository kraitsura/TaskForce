'use client';

import { Input } from "@/components/ui/input"
import { useState } from 'react';
import axios from 'axios';

interface SubTask {
  description: string;
  time_estimate: string;
}

interface StructureStep {
  step: string;
  details: string[];
  time_estimate: string;
}

interface ErrorObject {
  type?: string;
  loc?: string[];
  msg?: string;
  input?: any;
}

export function TaskInput() {
  const [task, setTask] = useState<string>('');
  const [subtasks, setSubtasks] = useState<SubTask[]>([]);
  const [selectedSubtasks, setSelectedSubtasks] = useState<number[]>([]);
  const [overallStructure, setOverallStructure] = useState<StructureStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await axios.post<SubTask[]>('http://localhost:8000/get_subtasks', { description: task });
      setSubtasks(response.data);
      setSelectedSubtasks([]);
      setOverallStructure([]);
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubtaskSelection = (index: number) => {
    setSelectedSubtasks(prev => 
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    );
  };

  const handleGetStructure = async () => {
    setError(null);
    setLoading(true);
    try {
      const selectedSubtaskData = selectedSubtasks.map(index => subtasks[index]);
      const response = await axios.post<StructureStep[]>('http://localhost:8000/get_overall_structure', { 
        selected_subtasks: selectedSubtaskData
      });
      setOverallStructure(response.data);
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  };

  const handleError = (error: unknown) => {
    if (axios.isAxiosError(error)) {
      if (error.response?.data) {
        const errorData = error.response.data as { msg: string };
        setError(errorData.msg || 'An error occurred while processing your request.');
      } else {
        setError('An error occurred while communicating with the server.');
      }
    } else {
      setError('An unexpected error occurred.');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4 text-white drop-shadow-md text-center">Welcome to TaskForce</h1>
      {error && <p className="text-red-500 mb-4 text-center bg-white/70 backdrop-blur-sm rounded-md p-2">{error}</p>}
      <form onSubmit={handleSubmit} className="mb-4 w-full max-w-md mx-auto">
        <Input
          type="text"
          value={task}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTask(e.target.value)}
          placeholder="Enter Task"
          className="w-full px-4 py-2 rounded-md border-2 border-transparent bg-white/70 backdrop-blur-sm focus:outline-none focus:border-blue-500 hover:bg-white/100 transition-colors duration-300"
        />
        <button 
          type="submit" 
          className="mt-2 w-full px-4 py-2 bg-blue-500 text-white rounded-md disabled:bg-blue-300 hover:bg-blue-600 transition-colors duration-300"
          disabled={loading || !task.trim()}
        >
          {loading ? 'Loading...' : 'Get Subtasks'}
        </button>
      </form>

      {subtasks.length > 0 && (
        <div className="mb-4 bg-white/70 backdrop-blur-sm rounded-md p-4">
          <h2 className="text-xl font-semibold mb-2">Subtasks:</h2>
          <ul>
            {subtasks.map((subtask, index) => (
              <li key={index} className="flex items-center mb-2">
                <input
                  type="checkbox"
                  checked={selectedSubtasks.includes(index)}
                  onChange={() => handleSubtaskSelection(index)}
                  className="mr-2"
                />
                <span>{subtask.description} - {subtask.time_estimate}</span>
              </li>
            ))}
          </ul>
          <button 
            onClick={handleGetStructure}
            className="mt-2 w-full px-4 py-2 bg-green-500 text-white rounded-md disabled:bg-green-300 hover:bg-green-600 transition-colors duration-300"
            disabled={loading || selectedSubtasks.length === 0}
          >
            {loading ? 'Loading...' : 'Get Overall Structure'}
          </button>
        </div>
      )}

      {overallStructure.length > 0 && (
        <div className="bg-white/70 backdrop-blur-sm rounded-md p-4">
          <h2 className="text-xl font-semibold mb-2">Overall Structure:</h2>
          {overallStructure.map((step, index) => (
            <div key={index} className="mb-4">
              <h3 className="font-semibold">{index + 1}. {step.step} - {step.time_estimate}</h3>
              <ul className="list-disc pl-5">
                {step.details.map((detail, detailIndex) => (
                  <li key={detailIndex}>{detail}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
