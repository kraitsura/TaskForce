import { TaskInput } from "@/components/task-input";


export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-br from-gray-900 to-black  bg-cover bg-center bg-no-repeat">
      <TaskInput />
    </div>
  );
}
