import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import StandardList from './pages/Standards/StandardList'
import StandardUpload from './pages/Standards/StandardUpload'
import StandardDetail from './pages/Standards/StandardDetail'
import SkillList from './pages/Skills/SkillList'
import SkillDetail from './pages/Skills/SkillDetail'
import SkillEditor from './pages/Skills/SkillEditor'
import MaterialParse from './pages/MaterialParse'
import KnowledgeGraph from './pages/KnowledgeGraph'
import ExecutionLogs from './pages/Observability/ExecutionLogs'
import Settings from './pages/Settings'
import { DatasetList, DatasetDetail, RunDetail } from './pages/Benchmark'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="standards" element={<StandardList />} />
        <Route path="standards/upload" element={<StandardUpload />} />
        <Route path="standards/:id" element={<StandardDetail />} />
        <Route path="skills" element={<SkillList />} />
        <Route path="skills/:skillId" element={<SkillDetail />} />
        <Route path="skills/:skillId/edit" element={<SkillEditor />} />
        <Route path="material-parse" element={<MaterialParse />} />
        <Route path="knowledge-graph" element={<KnowledgeGraph />} />
        <Route path="observability" element={<ExecutionLogs />} />
        <Route path="settings" element={<Settings />} />
        <Route path="benchmark/datasets" element={<DatasetList />} />
        <Route path="benchmark/datasets/:id" element={<DatasetDetail />} />
        <Route path="benchmark/runs/:id" element={<RunDetail />} />
      </Route>
    </Routes>
  )
}

export default App
